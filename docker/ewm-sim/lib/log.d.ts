declare const addColors: any, createLogger: any, format: any, transports: any;
declare const moment: any;
declare const path: any;
declare const PROJECT_ROOT: any;
declare const combine: any, timestamp: any, printf: any, json: any;
declare const myFormat: () => any;
declare const logger: any;
/**
 * Attempts to add file and line number info to the given log arguments.
 */
declare function formatLogArguments(args: any): any;
/**
 * Parses and returns info about the call stack at the given index.
 */
declare function getStackInfo(stackIndex: any): {
    method: string;
    relativePath: any;
    line: string;
    pos: string;
    file: any;
    stack: string;
} | undefined;
