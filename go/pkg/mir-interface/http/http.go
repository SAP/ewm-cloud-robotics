// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package http

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/apis"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig"
	"github.com/pkg/errors"
)

var log = zerologconfig.GetGlobalLogger()

// Client represents a HTTP client for MiR API
type Client struct {
	httpClient *http.Client
	baseURL    *url.URL
	username   string
	password   string
	userAgent  string
	maxRetries int
}

// NewClient returns a new client for MiR HTTP interface
func NewClient(host, basePath, username, password, userAgent string, timeoutSec float64) (*Client, error) {
	var err error

	client := &Client{userAgent: userAgent, username: username, password: password, maxRetries: 5}

	client.httpClient = &http.Client{Timeout: time.Duration(timeoutSec) * time.Second}

	client.baseURL, err = url.Parse(fmt.Sprintf("http://%s%s", host, basePath))
	if err != nil {
		return nil, errors.Wrap(err, "create baseURL")
	}

	return client, nil
}

// SetMaxRetries changes the number of retries on temporary errors (default is 5)
func (c *Client) SetMaxRetries(i int) *Client {
	if i >= 0 {
		c.maxRetries = i
	}
	return c
}

// Get performs a HTTP GET request to an arbitrary MiR interface endpoint
func (c *Client) Get(endpoint string, responseBody apis.MirResponse, errorBody apis.MirError) (*http.Response, error) {
	return c.getPostPutDelete(endpoint, "GET", nil, responseBody, errorBody)
}

// Put performs a HTTP PUT request to an arbitrary MiR interface endpoint
func (c *Client) Put(endpoint string, requestBody apis.MirRequest, responseBody apis.MirResponse, errorBody apis.MirError) (*http.Response, error) {
	return c.getPostPutDelete(endpoint, "PUT", requestBody, responseBody, errorBody)
}

// Post performs a HTTP POST request to an arbitrary MiR interface endpoint
func (c *Client) Post(endpoint string, requestBody apis.MirRequest, responseBody apis.MirResponse, errorBody apis.MirError) (*http.Response, error) {
	return c.getPostPutDelete(endpoint, "POST", requestBody, responseBody, errorBody)
}

// Delete performs a HTTP DELETE request to an arbitrary MiR interface endpoint
func (c *Client) Delete(endpoint string, errorBody apis.MirError) (*http.Response, error) {
	return c.getPostPutDelete(endpoint, "DELETE", nil, nil, errorBody)
}

func (c *Client) getPostPutDelete(endpoint, method string, requestBody apis.MirRequest, responseBody apis.MirResponse, errorBody apis.MirError) (*http.Response, error) {

	ref := &url.URL{Path: endpoint}

	var buf io.ReadWriter
	if requestBody != nil {
		buf = new(bytes.Buffer)
		err := json.NewEncoder(buf).Encode(requestBody)
		if err != nil {
			return nil, errors.Wrap(err, "encode JSON request body")
		}
	}

	req, err := http.NewRequest(method, c.baseURL.ResolveReference(ref).String(), buf)
	if err != nil {
		return nil, errors.Wrapf(err, "create new HTTP %s request", method)
	}

	req.SetBasicAuth(c.username, c.password)
	req.Header.Set("Accept", "application/json")
	if c.userAgent != "" {
		req.Header.Set("User-Agent", c.userAgent)
	}

	if requestBody != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	var returnResponse *http.Response
	var lastErr error

	for i := 0; i <= c.maxRetries; i++ {

		if lastErr != nil {
			log.Error().Err(lastErr).Msgf("Connection to endpoint %s failed - Retrying", c.baseURL.ResolveReference(ref).String())
		}

		resp, err := c.httpClient.Do(req)
		returnResponse = resp
		if err != nil {
			lastErr = errors.Wrapf(err, "do HTTP %s request", method)
			time.Sleep(500 * time.Millisecond)
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode >= 200 && resp.StatusCode <= 299 {
			if responseBody != nil {
				err = json.NewDecoder(resp.Body).Decode(responseBody)
			}
		} else if resp.StatusCode == 503 {
			// 503 is a common temporary error in MiR API. It occurs for example when the robot is docking
			lastErr = errors.New("HTTP status is 503 - MiR API not available")
			time.Sleep(1 * time.Second)
			continue
		} else if errorBody != nil {
			err = json.NewDecoder(resp.Body).Decode(errorBody)
		}

		if err != nil {
			lastErr = errors.Wrapf(err, "decode JSON response body, HTTP status %v", resp.StatusCode)
			time.Sleep(500 * time.Millisecond)
			continue
		}

		// No error
		lastErr = nil
		break
	}

	return returnResponse, lastErr
}
