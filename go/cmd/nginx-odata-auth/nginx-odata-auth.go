//
// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"syscall"
	"time"
)

type odataEndpoint struct {
	host     string
	basePath string
	newHost  string
	newPath  string
}

type odataBasicAuth struct {
	user     string
	password string
}

type odataOAuth struct {
	tokenEndpoint string
	clientID      string
	clientSecret  string
}

type odataOAuthReturn struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
	Scope       string `json:"scope,omitempty"`
}

const (
	filename string = "/odata/location.conf"
)

var (
	logTrace   *log.Logger
	logInfo    *log.Logger
	logWarning *log.Logger
	logError   *log.Logger
)

func init() {
	initLog(ioutil.Discard, os.Stdout, os.Stdout, os.Stderr)
}

func initLog(
	traceHandle io.Writer,
	infoHandle io.Writer,
	warningHandle io.Writer,
	errorHandle io.Writer) {

	logTrace = log.New(traceHandle,
		"TRACE: ",
		log.Ldate|log.Ltime|log.Lshortfile)

	logInfo = log.New(infoHandle,
		"INFO: ",
		log.Ldate|log.Ltime|log.Lshortfile)

	logWarning = log.New(warningHandle,
		"WARNING: ",
		log.Ldate|log.Ltime|log.Lshortfile)

	logError = log.New(errorHandle,
		"ERROR: ",
		log.Ldate|log.Ltime|log.Lshortfile)
}

func createOAuthHeader(auth *odataOAuth) (string, time.Duration, error) {
	// Create OAuth header with access_token from token endpoint
	// HTTP Request to token endpoint
	c := &http.Client{Timeout: time.Second * 5}

	req, err := http.NewRequest("POST", auth.tokenEndpoint, nil)
	if err != nil {
		logError.Fatalf("Unable to create HTTP POST request to token endpoint %s: %v", auth.tokenEndpoint, err)
	}
	req.SetBasicAuth(auth.clientID, auth.clientSecret)
	req.Header.Add("Accept", "application/json")

	resp, err := c.Do(req)
	if err != nil {
		return "", 0, fmt.Errorf("Error performing HTTP request to token endpoint %s: %v", auth.tokenEndpoint, err)
	}

	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", 0, fmt.Errorf("HTTP request to token endpoint %s returned status %v", auth.tokenEndpoint, resp.StatusCode)
	}

	// Unmarshal json response
	var tokenEndpointBody odataOAuthReturn
	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", 0, fmt.Errorf("Error reading body of HTTP POST to token endpoint %s: %v", auth.tokenEndpoint, err)
	}
	logTrace.Printf("Endpoint registry reply: %v", string(bodyBytes))
	err = json.Unmarshal(bodyBytes, &tokenEndpointBody)

	if err != nil {
		return "", 0, fmt.Errorf("Error decoding JSON body of HTTP POST to token endpoint %s: %v", auth.tokenEndpoint, err)
	}

	// Create auth header and duration for token refresh
	authHeader := fmt.Sprintf("%s %s", tokenEndpointBody.TokenType, tokenEndpointBody.AccessToken)
	// Refresh token 60 seconds before it expires
	refreshIn := time.Duration(tokenEndpointBody.ExpiresIn-60) * time.Second

	return authHeader, refreshIn, nil

}

func createODataConfig(endpoint *odataEndpoint, authHeader string) string {
	// Create nginx config for OData proxy including authorization header
	pathSplit := strings.Split(endpoint.basePath, "/")
	service := pathSplit[len(pathSplit)-1]
	if service == "" {
		logError.Fatalf("Could not extract service name from %s", endpoint.basePath)
	}

	cfgTemplate := "location /%s/ {\n" +
		"    proxy_pass https://%s%s/;\n" +
		"    proxy_set_header Authorization \"%s\";\n" +
		"    proxy_set_header Accept-Encoding \"\";\n" +
		"    sub_filter_once off;\n" +
		"    sub_filter_types *;\n" +
		"    sub_filter '%s' '%s';\n" +
		"    sub_filter '%s' '%s';\n" +
		"}"

	cfg := fmt.Sprintf(
		cfgTemplate, service, endpoint.host, endpoint.basePath, authHeader,
		endpoint.host, endpoint.newHost, endpoint.basePath, endpoint.newPath)
	return cfg
}

func updateBasicAuthConfig(endpoint *odataEndpoint, auth *odataBasicAuth) {
	// Creating nginx OData proxy config for Basic authorization case
	logInfo.Print("Creating Basic Auth nginx configuration")
	// Base64 encoding of user password
	userPwB64 := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%s", auth.user, auth.password)))
	authHeader := fmt.Sprintf("Basic %s", userPwB64)

	// Create OData config
	odataConfig := createODataConfig(endpoint, authHeader)

	// Write config to file
	logInfo.Print("Writing nginx OData proxy configuration to file")
	err := ioutil.WriteFile(filename, []byte(odataConfig), 0644)
	if err != nil {
		logError.Fatalf("Unable to write OData proxy configuration to %s: %v", filename, err)
	}

	// Reload nginx
	reloadNginx()

	logInfo.Print("Basic Auth nginx configuration created successfully")
}

func updateOAuthConfig(endpoint *odataEndpoint, auth *odataOAuth) <-chan time.Time {
	// Creating nginx OData proxy config for OAuth authorization case
	logInfo.Print("Refreshing OAuth token")
	// Get auth header from token endpoint
	authHeader, refreshIn, err := createOAuthHeader(auth)
	if err != nil {
		logError.Printf("Error refreshing OAuth token, retrying in 1 second: %v", err)
		return time.After(time.Second * 1)
	}

	// Create OData config
	odataConfig := createODataConfig(endpoint, authHeader)

	// Write config to file
	logInfo.Print("Writing nginx OData proxy configuration to file")
	err = ioutil.WriteFile(filename, []byte(odataConfig), 0644)
	if err != nil {
		logError.Fatalf("Unable to write OData proxy configuration to %s: %v", filename, err)
	}

	// Reload nginx
	reloadNginx()

	logInfo.Printf("OAuth token refresh successfull, next token refresh scheduled in %v minutes", refreshIn.Minutes())

	// Return channel which is called when token expires
	return time.After(refreshIn)
}

func reloadNginx() {
	logInfo.Print("Reloading nginx")
	err := exec.Command("/usr/sbin/nginx", "-s", "reload").Run()
	if err != nil {
		logError.Fatalf("Unable to reload nginx: %v", err)
	}
}

func startNginx() {
	args := os.Args[1:]
	logInfo.Printf("Starting nginx with command line arguments: %v", args)
	err := exec.Command("/usr/sbin/nginx", args...).Run()
	if err != nil {
		logError.Fatalf("Unable to start nginx: %v", err)
	}
}

func stopNginx() {
	logInfo.Print("Stopping nginx")
	err := exec.Command("/usr/sbin/nginx", "-s", "stop").Run()
	if err != nil {
		logError.Fatalf("Unable to stop nginx: %v", err)
	}
}

func main() {
	// App close channel
	interruptChan := make(chan os.Signal, 1)
	signal.Notify(interruptChan, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)

	// Channel to trigger OAuth Token refresh
	var refreshTokenChan <-chan time.Time

	// Start nginx
	startNginx()
	// Stopping nginx in the end
	defer stopNginx()

	// Read environment variables
	endpoint := &odataEndpoint{}
	basicAuth := &odataBasicAuth{}
	oAuth := &odataOAuth{}

	endpoint.newHost = os.Getenv("CLOUD_ROBOTICS_DOMAIN")
	if endpoint.newHost == "" {
		logError.Fatal("Environment variable CLOUD_ROBOTICS_DOMAIN is not set")
	} else {
		logInfo.Printf("CLOUD_ROBOTICS_DOMAIN is %s", endpoint.newHost)
	}
	endpoint.host = os.Getenv("ODATA_HOST")
	if endpoint.host == "" {
		logError.Fatal("Environment variable ODATA_HOST is not set")
	} else {
		logInfo.Printf("ODATA_HOST is %s", endpoint.host)
	}

	endpoint.basePath = os.Getenv("ODATA_BASEPATH")
	if endpoint.basePath == "" {
		logError.Fatal("Environment variable ODATA_BASEPATH is not set")
	} else {
		logInfo.Printf("ODATA_BASEPATH is %s", endpoint.basePath)
	}

	endpoint.newPath = os.Getenv("ODATA_NEWPATH")
	if endpoint.newPath == "" {
		logError.Fatal("Environment variable ODATA_NEWPATH is not set")
	} else {
		logInfo.Printf("ODATA_NEWPATH is %s", endpoint.newPath)
	}

	odataAuth := os.Getenv("ODATA_AUTH")
	if odataAuth == "Basic" {
		logInfo.Print("Using Basic Authorization for OData")
		basicAuth.user = os.Getenv("ODATA_USER")
		if basicAuth.user == "" {
			logError.Fatal("Environment variable ODATA_USER is not set")
		} else {
			logInfo.Printf("ODATA_USER is %s", basicAuth.user)
		}
		basicAuth.password = os.Getenv("ODATA_PASSWORD")
		if basicAuth.password == "" {
			logError.Fatal("Environment variable ODATA_PASSWORD is not set")
		} else {
			logInfo.Print("ODATA_PASSWORD is set")
		}

		// Basic auth case
		updateBasicAuthConfig(endpoint, basicAuth)

	} else if odataAuth == "OAuth" {
		logInfo.Print("Using OAuth Authorization for OData")
		oAuth.tokenEndpoint = os.Getenv("ODATA_TOKENENDPOINT")
		if oAuth.tokenEndpoint == "" {
			logError.Fatal("Environment variable ODATA_TOKENENDPOINT is not set")
		} else {
			logInfo.Printf("ODATA_TOKENENDPOINT is %s", oAuth.tokenEndpoint)
		}
		oAuth.clientID = os.Getenv("ODATA_CLIENTID")
		if oAuth.clientID == "" {
			logError.Fatal("Environment variable ODATA_CLIENTID is not set")
		} else {
			logInfo.Printf("ODATA_CLIENTID is %s", oAuth.clientID)
		}
		oAuth.clientSecret = os.Getenv("ODATA_CLIENTSECRET")
		if oAuth.clientSecret == "" {
			logError.Fatal("Environment variable ODATA_CLIENTSECRET is not set")
		} else {
			logInfo.Print("ODATA_CLIENTSECRET is set")
		}

		// OAuth case
		refreshTokenChan = updateOAuthConfig(endpoint, oAuth)

	} else {
		logError.Fatalf("Authentication %s is not supported", odataAuth)
	}

	// Main loop
	for running := true; running == true; {
		select {
		case <-interruptChan:
			// Stop app on SIGTERM
			running = false
		case <-refreshTokenChan:
			// Update nginx config with new authorization header when OAuth token expires
			if oAuth.tokenEndpoint == "" {
				logError.Fatal("Try to refresh OAuth token with no token endpoint set")
			}
			refreshTokenChan = updateOAuthConfig(endpoint, oAuth)
		}
	}

}
