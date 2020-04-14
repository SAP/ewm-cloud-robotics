// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package zerologconfig

import (
	"os"
	"strings"
	"time"

	"github.com/rs/zerolog"
)

// FilteredWriter filters zerolog messages by log level
type FilteredWriter struct {
	w        zerolog.LevelWriter
	minLevel zerolog.Level
	maxLevel zerolog.Level
}

// Write implements the io.Writer interface.
func (w *FilteredWriter) Write(p []byte) (n int, err error) {
	return w.w.Write(p)
}

// WriteLevel implements the LevelWriter interface.
func (w *FilteredWriter) WriteLevel(level zerolog.Level, p []byte) (n int, err error) {
	if level >= w.minLevel && level <= w.maxLevel {
		return w.w.WriteLevel(level, p)
	}
	return len(p), nil
}

// Severity hook for stackdriver
type severityHook struct{}

func (h severityHook) Run(e *zerolog.Event, level zerolog.Level, msg string) {
	if level != zerolog.NoLevel {
		e.Str("severity", level.String())
	}
}

// Log represents a global instance of Logger
var Log zerolog.Logger

func init() {
	// Initialize gobal Logger
	Log = *NewLogger()
}

// GetGlobalLogger returns the global instance of preconfigured zerolog Logger
func GetGlobalLogger() *zerolog.Logger {
	return &Log
}

// NewLogger return a new instance of preconfigured zerolog logger
func NewLogger() *zerolog.Logger {

	var log zerolog.Logger

	// JSON or console configuration
	json := bool(strings.ToLower(os.Getenv("ZEROLOG_CONFIG")) == "json")

	if json {
		log = zerolog.New(os.Stderr).Hook(severityHook{}).With().Timestamp().Caller().Logger()
		log.Info().Msg("Zerolog started with JSON config")
	} else {
		stdoutWriter := zerolog.MultiLevelWriter(zerolog.ConsoleWriter{Out: os.Stdout, NoColor: true, TimeFormat: time.RFC3339})
		stderrWriter := zerolog.MultiLevelWriter(zerolog.ConsoleWriter{Out: os.Stderr, NoColor: true, TimeFormat: time.RFC3339})
		infoWriter := &FilteredWriter{stdoutWriter, zerolog.TraceLevel, zerolog.WarnLevel}
		errorWriter := &FilteredWriter{stderrWriter, zerolog.ErrorLevel, zerolog.NoLevel}
		mainWriter := zerolog.MultiLevelWriter(infoWriter, errorWriter)
		log = zerolog.New(mainWriter).With().Timestamp().Caller().Logger()
		log.Info().Msg("Zerolog started with CONSOLE config")
	}

	// Default global log level is info
	zerolog.SetGlobalLevel(zerolog.InfoLevel)
	logLevel := strings.ToLower(os.Getenv("ZEROLOG_LOGLEVEL"))
	if logLevel != "" {
		zerologLevel, err := zerolog.ParseLevel(logLevel)
		if err == nil {
			zerolog.SetGlobalLevel(zerologLevel)
		}
	}

	log.Info().Msgf("Global log level set to \"%s\"", zerolog.GlobalLevel())

	return &log

}
