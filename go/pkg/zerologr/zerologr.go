// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

// This is an implementation of logr interface for zerolog
// https://github.com/go-logr/logr/blob/master/logr.go - currently in v0.3.0

package zerologr

import (
	"fmt"

	"github.com/go-logr/logr"
	"github.com/rs/zerolog"
)

type keyVal struct {
	key string
	val interface{}
}

type zerologLogger struct {
	l      *zerolog.Logger
	lvl    zerolog.Level
	name   string
	noName *zerolog.Logger
}

// handleKeysAndValues handles key-value pairs which follow the logr interface specifications
func handleKeysAndValues(l *zerolog.Logger, keysAndValues []interface{}) []keyVal {

	keyVals := make([]keyVal, 0, len(keysAndValues)/2)

	for i := 0; i < len(keysAndValues); {

		if i == len(keysAndValues)-1 {
			l.Error().Msgf("odd number of arguments passed as key-value pairs for logging. Ignored key: %s", keysAndValues[i])
			break
		}

		key, val := keysAndValues[i], keysAndValues[i+1]
		keyStr, isString := key.(string)

		if !isString {
			l.Error().Msgf("A non-string key argument passed to logging, skip entry: %v/%v", key, val)
			continue
		}

		keyVal := keyVal{key: keyStr, val: val}
		keyVals = append(keyVals, keyVal)

		i += 2
	}

	return keyVals
}

// Enabled implements a method of logr interface
func (zl *zerologLogger) Enabled() bool {
	if zl.lvl < zl.l.GetLevel() || zl.lvl < zerolog.GlobalLevel() {
		return false
	}
	return true
}

// Info implements a method of logr interface
func (zl *zerologLogger) Info(msg string, keysAndValues ...interface{}) {
	e := zl.l.WithLevel(zl.lvl)

	keyVals := handleKeysAndValues(zl.l, keysAndValues)
	for _, keyVal := range keyVals {
		e = e.Interface(keyVal.key, keyVal.val)
	}

	e.Msg(msg)
}

// Error implements a method of logr interface
func (zl *zerologLogger) Error(err error, msg string, keysAndValues ...interface{}) {
	e := zl.l.Error().Err(err)

	keyVals := handleKeysAndValues(zl.l, keysAndValues)
	for _, keyVal := range keyVals {
		e = e.Interface(keyVal.key, keyVal.val)
	}

	e.Msg(msg)
}

// V implements a method of logr interface
func (zl *zerologLogger) V(level int) logr.InfoLogger {
	return &zerologLogger{
		lvl: zl.lvl - zerolog.Level(level),
		l:   zl.l,
	}
}

// WithValues implements a method of logr interface
func (zl *zerologLogger) WithValues(keysAndValues ...interface{}) logr.Logger {
	newLogger := &zerologLogger{lvl: zl.lvl}

	zCtx := zl.l.With()

	keyVals := handleKeysAndValues(zl.l, keysAndValues)
	for _, keyVal := range keyVals {
		zCtx = zCtx.Interface(keyVal.key, keyVal.val)
	}

	zlLogger := zCtx.Logger()
	newLogger.l = &zlLogger

	return newLogger
}

// WithName implements a method of logr interface
// It appends ".name" to the existing name or creates a new one
func (zl *zerologLogger) WithName(name string) logr.Logger {
	newLogger := &zerologLogger{lvl: zl.lvl, noName: zl.noName}
	if zl.name == "" {
		newLogger.name = name
	} else {
		newLogger.name = fmt.Sprintf("%s.%s", zl.name, name)
	}

	zlLogger := zl.noName.With().Str("logger", newLogger.name).Logger()
	newLogger.l = &zlLogger

	return newLogger
}

// NewLogger creates a new logr.Logger using the given zerolog logger
func NewLogger(l *zerolog.Logger) logr.Logger {
	return &zerologLogger{l: l, lvl: zerolog.InfoLevel, noName: l}
}
