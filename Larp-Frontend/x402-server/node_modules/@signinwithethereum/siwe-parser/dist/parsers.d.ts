export declare type AddressCaseStatus = 'valid-checksum' | 'unchecksummed' | 'invalid-checksum';

export declare const classifyAddressCase: (address: string) => AddressCaseStatus;

/**
 * Check whether an address matches its EIP-55 checksum.
 * @param address Address to be checked if conforms with EIP-55.
 * @returns Whether the address is in EIP-55 checksummed form.
 */
export declare const isEIP55Address: (address: string) => boolean;

export declare const isUri: (uri: string) => any;

export declare const isValidISO8601Date: (inputDate: string) => boolean;

export declare class ParsedMessage {
    scheme: string | undefined;
    domain: string;
    address: string;
    statement: string | undefined;
    uri: string;
    version: string;
    chainId: number;
    nonce: string;
    issuedAt: string;
    expirationTime: string | undefined;
    notBefore: string | undefined;
    requestId: string | undefined;
    resources: string[] | undefined;
    uriElements: {
        scheme: string;
        userinfo: string | undefined;
        host: string | undefined;
        port: string | undefined;
        path: string;
        query: string | undefined;
        fragment: string | undefined;
    };
    /** Non-fatal warnings from parsing (e.g. unchecksummed address). */
    warnings: string[];
    constructor(msg: string);
}

export declare const parseIntegerNumber: (number: string) => number;

/**
 * Structured error for SIWE message parsing failures.
 * Collects all individual validation errors encountered during parsing.
 */
export declare class SiweParseError extends Error {
    /** Individual error messages collected during parsing. */
    readonly errors: string[];
    constructor(errors: string[]);
}

/**
 * Encode an address with the EIP-55 mixed-case checksum.
 * Accepts any-case hex input; returns the canonical checksummed form.
 */
export declare const toChecksumAddress: (address: string) => string;

export { }
