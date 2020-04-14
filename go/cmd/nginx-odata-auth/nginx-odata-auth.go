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
	"context"
	"encoding/base64"
	"fmt"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig"
	"golang.org/x/oauth2/clientcredentials"
	"io/ioutil"
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

const (
	filename string = "/odata/location.conf"
)

var log = zerologconfig.GetGlobalLogger()

func createODataConfig(endpoint *odataEndpoint, authHeader string) string {
	// Create nginx config for OData proxy including authorization header
	pathSplit := strings.Split(endpoint.basePath, "/")
	service := pathSplit[len(pathSplit)-1]
	if service == "" {
		log.Fatal().Msgf("Could not extract service name from %s", endpoint.basePath)
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
	log.Info().Msg("Creating Basic Auth nginx configuration")
	// Base64 encoding of user password
	userPwB64 := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%s", auth.user, auth.password)))
	authHeader := fmt.Sprintf("Basic %s", userPwB64)

	// Create OData config
	odataConfig := createODataConfig(endpoint, authHeader)

	// Write config to file
	log.Info().Msg("Writing nginx OData proxy configuration to file")
	err := ioutil.WriteFile(filename, []byte(odataConfig), 0644)
	if err != nil {
		log.Fatal().Err(err).Msgf("Unable to write OData proxy configuration to %s", filename)
	}

	// Reload nginx
	reloadNginx()

	log.Info().Msg("Basic Auth nginx configuration created successfully")
}

func updateOAuthConfig(ctx context.Context, endpoint *odataEndpoint, auth *clientcredentials.Config) <-chan time.Time {
	// Creating nginx OData proxy config for OAuth authorization case
	log.Info().Msg("Refreshing OAuth token")
	// Get auth header from token endpoint

	token, err := auth.Token(ctx)
	if err != nil {
		log.Error().Err(err).Msg("Error refreshing OAuth token, retrying in 1 second")
		return time.After(time.Second * 1)
	}

	// Create auth header
	authHeader := fmt.Sprintf("%s %s", token.TokenType, token.AccessToken)

	// Create OData config
	odataConfig := createODataConfig(endpoint, authHeader)

	// Write config to file
	log.Info().Msg("Writing nginx OData proxy configuration to file")
	err = ioutil.WriteFile(filename, []byte(odataConfig), 0644)
	if err != nil {
		log.Fatal().Err(err).Msgf("Unable to write OData proxy configuration to %s", filename)
	}

	// Reload nginx
	reloadNginx()

	refresh := token.Expiry.Sub(time.Now()) - time.Duration(time.Minute*1)
	log.Info().Msgf("OAuth token refresh successfull, next token refresh scheduled in %v minutes", refresh.Minutes())

	// Return channel which is called when token expires
	return time.After(refresh)
}

func reloadNginx() {
	log.Info().Msg("Reloading nginx")
	err := exec.Command("/usr/sbin/nginx", "-s", "reload").Run()
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to reload nginx")
	}
}

func startNginx() {
	args := os.Args[1:]
	log.Info().Msgf("Starting nginx with command line arguments: %v", args)
	err := exec.Command("/usr/sbin/nginx", args...).Run()
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to start nginx")
	}
}

func stopNginx() {
	log.Info().Msg("Stopping nginx")
	err := exec.Command("/usr/sbin/nginx", "-s", "stop").Run()
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to stop nginx")
	}
}

func main() {
	// App close channel
	interruptChan := make(chan os.Signal, 1)
	signal.Notify(interruptChan, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)

	// Context
	ctx := context.Background()

	// Channel to trigger OAuth Token refresh
	var refreshTokenChan <-chan time.Time

	// Start nginx
	startNginx()
	// Stopping nginx in the end
	defer stopNginx()

	// Read environment variables
	endpoint := &odataEndpoint{}
	basicAuth := &odataBasicAuth{}
	oAuth := &clientcredentials.Config{}

	endpoint.newHost = os.Getenv("CLOUD_ROBOTICS_DOMAIN")
	if endpoint.newHost == "" {
		log.Fatal().Msg("Environment variable CLOUD_ROBOTICS_DOMAIN is not set")
	} else {
		log.Info().Msgf("CLOUD_ROBOTICS_DOMAIN is %s", endpoint.newHost)
	}
	endpoint.host = os.Getenv("ODATA_HOST")
	if endpoint.host == "" {
		log.Fatal().Msg("Environment variable ODATA_HOST is not set")
	} else {
		log.Info().Msgf("ODATA_HOST is %s", endpoint.host)
	}

	endpoint.basePath = os.Getenv("ODATA_BASEPATH")
	if endpoint.basePath == "" {
		log.Fatal().Msg("Environment variable ODATA_BASEPATH is not set")
	} else {
		log.Info().Msgf("ODATA_BASEPATH is %s", endpoint.basePath)
	}

	endpoint.newPath = os.Getenv("ODATA_NEWPATH")
	if endpoint.newPath == "" {
		log.Fatal().Msg("Environment variable ODATA_NEWPATH is not set")
	} else {
		log.Info().Msgf("ODATA_NEWPATH is %s", endpoint.newPath)
	}

	odataAuth := os.Getenv("ODATA_AUTH")
	if odataAuth == "Basic" {
		log.Info().Msg("Using Basic Authorization for OData")
		basicAuth.user = os.Getenv("ODATA_USER")
		if basicAuth.user == "" {
			log.Fatal().Msg("Environment variable ODATA_USER is not set")
		} else {
			log.Info().Msgf("ODATA_USER is %s", basicAuth.user)
		}
		basicAuth.password = os.Getenv("ODATA_PASSWORD")
		if basicAuth.password == "" {
			log.Fatal().Msg("Environment variable ODATA_PASSWORD is not set")
		} else {
			log.Info().Msg("ODATA_PASSWORD is set")
		}

		// Basic auth case
		updateBasicAuthConfig(endpoint, basicAuth)

	} else if odataAuth == "OAuth" {
		log.Info().Msg("Using OAuth Authorization for OData")
		oAuth.TokenURL = os.Getenv("ODATA_TOKENENDPOINT")
		if oAuth.TokenURL == "" {
			log.Fatal().Msg("Environment variable ODATA_TOKENENDPOINT is not set")
		} else {
			log.Info().Msgf("ODATA_TOKENENDPOINT is %s", oAuth.TokenURL)
		}
		oAuth.ClientID = os.Getenv("ODATA_CLIENTID")
		if oAuth.ClientID == "" {
			log.Fatal().Msg("Environment variable ODATA_CLIENTID is not set")
		} else {
			log.Info().Msgf("ODATA_CLIENTID is %s", oAuth.ClientID)
		}
		oAuth.ClientSecret = os.Getenv("ODATA_CLIENTSECRET")
		if oAuth.ClientSecret == "" {
			log.Fatal().Msg("Environment variable ODATA_CLIENTSECRET is not set")
		} else {
			log.Info().Msg("ODATA_CLIENTSECRET is set")
		}

		// OAuth case
		refreshTokenChan = updateOAuthConfig(ctx, endpoint, oAuth)

	} else {
		log.Fatal().Msgf("Authentication %s is not supported", odataAuth)
	}

	// Main loop
	for running := true; running == true; {
		select {
		case <-interruptChan:
			// Stop app on SIGTERM
			running = false
		case <-refreshTokenChan:
			// Update nginx config with new authorization header when OAuth token expires
			if oAuth.TokenURL == "" {
				log.Fatal().Msg("Try to refresh OAuth token with no token endpoint set")
			}
			refreshTokenChan = updateOAuthConfig(ctx, endpoint, oAuth)
		}
	}

}
