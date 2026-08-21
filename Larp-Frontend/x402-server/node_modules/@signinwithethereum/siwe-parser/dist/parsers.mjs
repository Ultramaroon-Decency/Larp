import e from "apg-js/src/apg-lib/node-exports.js";
import { keccak_256 as t } from "@noble/hashes/sha3";
import { bytesToHex as n } from "@noble/hashes/utils";
//#region lib/siwe-grammar.ts
function r() {
	this.grammarObject = "grammarObject", this.rules = [], this.rules[0] = {
		name: "sign-in-with-ethereum",
		lower: "sign-in-with-ethereum",
		index: 0,
		isBkr: !1
	}, this.rules[1] = {
		name: "ex-title",
		lower: "ex-title",
		index: 1,
		isBkr: !1
	}, this.rules[2] = {
		name: "nb-title",
		lower: "nb-title",
		index: 2,
		isBkr: !1
	}, this.rules[3] = {
		name: "ri-title",
		lower: "ri-title",
		index: 3,
		isBkr: !1
	}, this.rules[4] = {
		name: "re-title",
		lower: "re-title",
		index: 4,
		isBkr: !1
	}, this.rules[5] = {
		name: "oscheme",
		lower: "oscheme",
		index: 5,
		isBkr: !1
	}, this.rules[6] = {
		name: "domain",
		lower: "domain",
		index: 6,
		isBkr: !1
	}, this.rules[7] = {
		name: "address",
		lower: "address",
		index: 7,
		isBkr: !1
	}, this.rules[8] = {
		name: "statement",
		lower: "statement",
		index: 8,
		isBkr: !1
	}, this.rules[9] = {
		name: "empty-statement",
		lower: "empty-statement",
		index: 9,
		isBkr: !1
	}, this.rules[10] = {
		name: "version",
		lower: "version",
		index: 10,
		isBkr: !1
	}, this.rules[11] = {
		name: "nonce",
		lower: "nonce",
		index: 11,
		isBkr: !1
	}, this.rules[12] = {
		name: "issued-at",
		lower: "issued-at",
		index: 12,
		isBkr: !1
	}, this.rules[13] = {
		name: "expiration-time",
		lower: "expiration-time",
		index: 13,
		isBkr: !1
	}, this.rules[14] = {
		name: "not-before",
		lower: "not-before",
		index: 14,
		isBkr: !1
	}, this.rules[15] = {
		name: "request-id",
		lower: "request-id",
		index: 15,
		isBkr: !1
	}, this.rules[16] = {
		name: "chain-id",
		lower: "chain-id",
		index: 16,
		isBkr: !1
	}, this.rules[17] = {
		name: "resources",
		lower: "resources",
		index: 17,
		isBkr: !1
	}, this.rules[18] = {
		name: "resource",
		lower: "resource",
		index: 18,
		isBkr: !1
	}, this.rules[19] = {
		name: "URI",
		lower: "uri",
		index: 19,
		isBkr: !1
	}, this.rules[20] = {
		name: "hier-part",
		lower: "hier-part",
		index: 20,
		isBkr: !1
	}, this.rules[21] = {
		name: "scheme",
		lower: "scheme",
		index: 21,
		isBkr: !1
	}, this.rules[22] = {
		name: "authority",
		lower: "authority",
		index: 22,
		isBkr: !1
	}, this.rules[23] = {
		name: "path-abempty",
		lower: "path-abempty",
		index: 23,
		isBkr: !1
	}, this.rules[24] = {
		name: "path-absolute",
		lower: "path-absolute",
		index: 24,
		isBkr: !1
	}, this.rules[25] = {
		name: "path-rootless",
		lower: "path-rootless",
		index: 25,
		isBkr: !1
	}, this.rules[26] = {
		name: "path-empty",
		lower: "path-empty",
		index: 26,
		isBkr: !1
	}, this.rules[27] = {
		name: "userinfo-at",
		lower: "userinfo-at",
		index: 27,
		isBkr: !1
	}, this.rules[28] = {
		name: "userinfo",
		lower: "userinfo",
		index: 28,
		isBkr: !1
	}, this.rules[29] = {
		name: "host",
		lower: "host",
		index: 29,
		isBkr: !1
	}, this.rules[30] = {
		name: "IP-literal",
		lower: "ip-literal",
		index: 30,
		isBkr: !1
	}, this.rules[31] = {
		name: "IPvFuture",
		lower: "ipvfuture",
		index: 31,
		isBkr: !1
	}, this.rules[32] = {
		name: "IPv6address",
		lower: "ipv6address",
		index: 32,
		isBkr: !1
	}, this.rules[33] = {
		name: "nodcolon",
		lower: "nodcolon",
		index: 33,
		isBkr: !1
	}, this.rules[34] = {
		name: "dcolon",
		lower: "dcolon",
		index: 34,
		isBkr: !1
	}, this.rules[35] = {
		name: "h16",
		lower: "h16",
		index: 35,
		isBkr: !1
	}, this.rules[36] = {
		name: "h16c",
		lower: "h16c",
		index: 36,
		isBkr: !1
	}, this.rules[37] = {
		name: "h16n",
		lower: "h16n",
		index: 37,
		isBkr: !1
	}, this.rules[38] = {
		name: "h16cn",
		lower: "h16cn",
		index: 38,
		isBkr: !1
	}, this.rules[39] = {
		name: "IPv4address",
		lower: "ipv4address",
		index: 39,
		isBkr: !1
	}, this.rules[40] = {
		name: "dec-octet",
		lower: "dec-octet",
		index: 40,
		isBkr: !1
	}, this.rules[41] = {
		name: "dec-digit",
		lower: "dec-digit",
		index: 41,
		isBkr: !1
	}, this.rules[42] = {
		name: "reg-name",
		lower: "reg-name",
		index: 42,
		isBkr: !1
	}, this.rules[43] = {
		name: "reg-name-char",
		lower: "reg-name-char",
		index: 43,
		isBkr: !1
	}, this.rules[44] = {
		name: "port",
		lower: "port",
		index: 44,
		isBkr: !1
	}, this.rules[45] = {
		name: "query",
		lower: "query",
		index: 45,
		isBkr: !1
	}, this.rules[46] = {
		name: "fragment",
		lower: "fragment",
		index: 46,
		isBkr: !1
	}, this.rules[47] = {
		name: "URI-r",
		lower: "uri-r",
		index: 47,
		isBkr: !1
	}, this.rules[48] = {
		name: "hier-part-r",
		lower: "hier-part-r",
		index: 48,
		isBkr: !1
	}, this.rules[49] = {
		name: "scheme-r",
		lower: "scheme-r",
		index: 49,
		isBkr: !1
	}, this.rules[50] = {
		name: "query-r",
		lower: "query-r",
		index: 50,
		isBkr: !1
	}, this.rules[51] = {
		name: "fragment-r",
		lower: "fragment-r",
		index: 51,
		isBkr: !1
	}, this.rules[52] = {
		name: "authority-d",
		lower: "authority-d",
		index: 52,
		isBkr: !1
	}, this.rules[53] = {
		name: "userinfo-d",
		lower: "userinfo-d",
		index: 53,
		isBkr: !1
	}, this.rules[54] = {
		name: "host-d",
		lower: "host-d",
		index: 54,
		isBkr: !1
	}, this.rules[55] = {
		name: "port-d",
		lower: "port-d",
		index: 55,
		isBkr: !1
	}, this.rules[56] = {
		name: "path-abempty-r",
		lower: "path-abempty-r",
		index: 56,
		isBkr: !1
	}, this.rules[57] = {
		name: "path-absolute-r",
		lower: "path-absolute-r",
		index: 57,
		isBkr: !1
	}, this.rules[58] = {
		name: "path-rootless-r",
		lower: "path-rootless-r",
		index: 58,
		isBkr: !1
	}, this.rules[59] = {
		name: "path-empty-r",
		lower: "path-empty-r",
		index: 59,
		isBkr: !1
	}, this.rules[60] = {
		name: "segment",
		lower: "segment",
		index: 60,
		isBkr: !1
	}, this.rules[61] = {
		name: "segment-nz",
		lower: "segment-nz",
		index: 61,
		isBkr: !1
	}, this.rules[62] = {
		name: "pchar",
		lower: "pchar",
		index: 62,
		isBkr: !1
	}, this.rules[63] = {
		name: "pct-encoded",
		lower: "pct-encoded",
		index: 63,
		isBkr: !1
	}, this.rules[64] = {
		name: "date-fullyear",
		lower: "date-fullyear",
		index: 64,
		isBkr: !1
	}, this.rules[65] = {
		name: "date-month",
		lower: "date-month",
		index: 65,
		isBkr: !1
	}, this.rules[66] = {
		name: "date-mday",
		lower: "date-mday",
		index: 66,
		isBkr: !1
	}, this.rules[67] = {
		name: "time-hour",
		lower: "time-hour",
		index: 67,
		isBkr: !1
	}, this.rules[68] = {
		name: "time-minute",
		lower: "time-minute",
		index: 68,
		isBkr: !1
	}, this.rules[69] = {
		name: "time-second",
		lower: "time-second",
		index: 69,
		isBkr: !1
	}, this.rules[70] = {
		name: "time-secfrac",
		lower: "time-secfrac",
		index: 70,
		isBkr: !1
	}, this.rules[71] = {
		name: "time-numoffset",
		lower: "time-numoffset",
		index: 71,
		isBkr: !1
	}, this.rules[72] = {
		name: "time-offset",
		lower: "time-offset",
		index: 72,
		isBkr: !1
	}, this.rules[73] = {
		name: "partial-time",
		lower: "partial-time",
		index: 73,
		isBkr: !1
	}, this.rules[74] = {
		name: "full-date",
		lower: "full-date",
		index: 74,
		isBkr: !1
	}, this.rules[75] = {
		name: "full-time",
		lower: "full-time",
		index: 75,
		isBkr: !1
	}, this.rules[76] = {
		name: "date-time",
		lower: "date-time",
		index: 76,
		isBkr: !1
	}, this.rules[77] = {
		name: "ALPHA",
		lower: "alpha",
		index: 77,
		isBkr: !1
	}, this.rules[78] = {
		name: "LF",
		lower: "lf",
		index: 78,
		isBkr: !1
	}, this.rules[79] = {
		name: "DIGIT",
		lower: "digit",
		index: 79,
		isBkr: !1
	}, this.rules[80] = {
		name: "HEXDIG",
		lower: "hexdig",
		index: 80,
		isBkr: !1
	}, this.udts = [], this.rules[0].opcodes = [], this.rules[0].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3,
			4,
			5,
			6,
			7,
			17,
			18,
			19,
			20,
			21,
			22,
			23,
			24,
			25,
			26,
			27,
			28,
			29,
			30,
			31,
			36,
			41,
			46
		]
	}, this.rules[0].opcodes[1] = {
		type: 4,
		index: 5
	}, this.rules[0].opcodes[2] = {
		type: 4,
		index: 6
	}, this.rules[0].opcodes[3] = {
		type: 6,
		string: [
			32,
			119,
			97,
			110,
			116,
			115,
			32,
			121,
			111,
			117,
			32,
			116,
			111,
			32,
			115,
			105,
			103,
			110,
			32,
			105,
			110,
			32,
			119,
			105,
			116,
			104,
			32,
			121,
			111,
			117,
			114,
			32,
			69,
			116,
			104,
			101,
			114,
			101,
			117,
			109,
			32,
			97,
			99,
			99,
			111,
			117,
			110,
			116,
			58
		]
	}, this.rules[0].opcodes[4] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[5] = {
		type: 4,
		index: 7
	}, this.rules[0].opcodes[6] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[7] = {
		type: 1,
		children: [
			8,
			13,
			14
		]
	}, this.rules[0].opcodes[8] = {
		type: 2,
		children: [
			9,
			10,
			11,
			12
		]
	}, this.rules[0].opcodes[9] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[10] = {
		type: 4,
		index: 8
	}, this.rules[0].opcodes[11] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[12] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[13] = {
		type: 4,
		index: 9
	}, this.rules[0].opcodes[14] = {
		type: 2,
		children: [15, 16]
	}, this.rules[0].opcodes[15] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[16] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[17] = {
		type: 6,
		string: [
			85,
			82,
			73,
			58,
			32
		]
	}, this.rules[0].opcodes[18] = {
		type: 4,
		index: 19
	}, this.rules[0].opcodes[19] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[20] = {
		type: 6,
		string: [
			86,
			101,
			114,
			115,
			105,
			111,
			110,
			58,
			32
		]
	}, this.rules[0].opcodes[21] = {
		type: 4,
		index: 10
	}, this.rules[0].opcodes[22] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[23] = {
		type: 6,
		string: [
			67,
			104,
			97,
			105,
			110,
			32,
			73,
			68,
			58,
			32
		]
	}, this.rules[0].opcodes[24] = {
		type: 4,
		index: 16
	}, this.rules[0].opcodes[25] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[26] = {
		type: 6,
		string: [
			78,
			111,
			110,
			99,
			101,
			58,
			32
		]
	}, this.rules[0].opcodes[27] = {
		type: 4,
		index: 11
	}, this.rules[0].opcodes[28] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[29] = {
		type: 6,
		string: [
			73,
			115,
			115,
			117,
			101,
			100,
			32,
			65,
			116,
			58,
			32
		]
	}, this.rules[0].opcodes[30] = {
		type: 4,
		index: 12
	}, this.rules[0].opcodes[31] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[0].opcodes[32] = {
		type: 2,
		children: [
			33,
			34,
			35
		]
	}, this.rules[0].opcodes[33] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[34] = {
		type: 4,
		index: 1
	}, this.rules[0].opcodes[35] = {
		type: 4,
		index: 13
	}, this.rules[0].opcodes[36] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[0].opcodes[37] = {
		type: 2,
		children: [
			38,
			39,
			40
		]
	}, this.rules[0].opcodes[38] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[39] = {
		type: 4,
		index: 2
	}, this.rules[0].opcodes[40] = {
		type: 4,
		index: 14
	}, this.rules[0].opcodes[41] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[0].opcodes[42] = {
		type: 2,
		children: [
			43,
			44,
			45
		]
	}, this.rules[0].opcodes[43] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[44] = {
		type: 4,
		index: 3
	}, this.rules[0].opcodes[45] = {
		type: 4,
		index: 15
	}, this.rules[0].opcodes[46] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[0].opcodes[47] = {
		type: 2,
		children: [
			48,
			49,
			50
		]
	}, this.rules[0].opcodes[48] = {
		type: 4,
		index: 78
	}, this.rules[0].opcodes[49] = {
		type: 4,
		index: 4
	}, this.rules[0].opcodes[50] = {
		type: 4,
		index: 17
	}, this.rules[1].opcodes = [], this.rules[1].opcodes[0] = {
		type: 6,
		string: [
			69,
			120,
			112,
			105,
			114,
			97,
			116,
			105,
			111,
			110,
			32,
			84,
			105,
			109,
			101,
			58,
			32
		]
	}, this.rules[2].opcodes = [], this.rules[2].opcodes[0] = {
		type: 6,
		string: [
			78,
			111,
			116,
			32,
			66,
			101,
			102,
			111,
			114,
			101,
			58,
			32
		]
	}, this.rules[3].opcodes = [], this.rules[3].opcodes[0] = {
		type: 6,
		string: [
			82,
			101,
			113,
			117,
			101,
			115,
			116,
			32,
			73,
			68,
			58,
			32
		]
	}, this.rules[4].opcodes = [], this.rules[4].opcodes[0] = {
		type: 6,
		string: [
			82,
			101,
			115,
			111,
			117,
			114,
			99,
			101,
			115,
			58
		]
	}, this.rules[5].opcodes = [], this.rules[5].opcodes[0] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[5].opcodes[1] = {
		type: 2,
		children: [
			2,
			3,
			9
		]
	}, this.rules[5].opcodes[2] = {
		type: 4,
		index: 77
	}, this.rules[5].opcodes[3] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[5].opcodes[4] = {
		type: 1,
		children: [
			5,
			6,
			7,
			8
		]
	}, this.rules[5].opcodes[5] = {
		type: 4,
		index: 77
	}, this.rules[5].opcodes[6] = {
		type: 4,
		index: 79
	}, this.rules[5].opcodes[7] = {
		type: 6,
		string: [43]
	}, this.rules[5].opcodes[8] = {
		type: 5,
		min: 45,
		max: 46
	}, this.rules[5].opcodes[9] = {
		type: 7,
		string: [
			58,
			47,
			47
		]
	}, this.rules[6].opcodes = [], this.rules[6].opcodes[0] = {
		type: 4,
		index: 52
	}, this.rules[7].opcodes = [], this.rules[7].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[7].opcodes[1] = {
		type: 7,
		string: [48, 120]
	}, this.rules[7].opcodes[2] = {
		type: 3,
		min: 40,
		max: 40
	}, this.rules[7].opcodes[3] = {
		type: 4,
		index: 80
	}, this.rules[8].opcodes = [], this.rules[8].opcodes[0] = {
		type: 3,
		min: 1,
		max: Infinity
	}, this.rules[8].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4,
			5,
			6,
			7,
			8,
			9,
			10,
			11,
			12,
			13
		]
	}, this.rules[8].opcodes[2] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[8].opcodes[3] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[8].opcodes[4] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[8].opcodes[5] = {
		type: 5,
		min: 32,
		max: 33
	}, this.rules[8].opcodes[6] = {
		type: 5,
		min: 35,
		max: 36
	}, this.rules[8].opcodes[7] = {
		type: 5,
		min: 38,
		max: 59
	}, this.rules[8].opcodes[8] = {
		type: 6,
		string: [61]
	}, this.rules[8].opcodes[9] = {
		type: 5,
		min: 63,
		max: 64
	}, this.rules[8].opcodes[10] = {
		type: 6,
		string: [91]
	}, this.rules[8].opcodes[11] = {
		type: 6,
		string: [93]
	}, this.rules[8].opcodes[12] = {
		type: 6,
		string: [95]
	}, this.rules[8].opcodes[13] = {
		type: 6,
		string: [126]
	}, this.rules[9].opcodes = [], this.rules[9].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3
		]
	}, this.rules[9].opcodes[1] = {
		type: 4,
		index: 78
	}, this.rules[9].opcodes[2] = {
		type: 4,
		index: 78
	}, this.rules[9].opcodes[3] = {
		type: 4,
		index: 78
	}, this.rules[10].opcodes = [], this.rules[10].opcodes[0] = {
		type: 7,
		string: [49]
	}, this.rules[11].opcodes = [], this.rules[11].opcodes[0] = {
		type: 3,
		min: 8,
		max: Infinity
	}, this.rules[11].opcodes[1] = {
		type: 1,
		children: [2, 3]
	}, this.rules[11].opcodes[2] = {
		type: 4,
		index: 77
	}, this.rules[11].opcodes[3] = {
		type: 4,
		index: 79
	}, this.rules[12].opcodes = [], this.rules[12].opcodes[0] = {
		type: 4,
		index: 76
	}, this.rules[13].opcodes = [], this.rules[13].opcodes[0] = {
		type: 4,
		index: 76
	}, this.rules[14].opcodes = [], this.rules[14].opcodes[0] = {
		type: 4,
		index: 76
	}, this.rules[15].opcodes = [], this.rules[15].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[15].opcodes[1] = {
		type: 4,
		index: 62
	}, this.rules[16].opcodes = [], this.rules[16].opcodes[0] = {
		type: 3,
		min: 1,
		max: Infinity
	}, this.rules[16].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[17].opcodes = [], this.rules[17].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[17].opcodes[1] = {
		type: 2,
		children: [2, 3]
	}, this.rules[17].opcodes[2] = {
		type: 4,
		index: 78
	}, this.rules[17].opcodes[3] = {
		type: 4,
		index: 18
	}, this.rules[18].opcodes = [], this.rules[18].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[18].opcodes[1] = {
		type: 7,
		string: [45, 32]
	}, this.rules[18].opcodes[2] = {
		type: 4,
		index: 47
	}, this.rules[19].opcodes = [], this.rules[19].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3,
			4,
			8
		]
	}, this.rules[19].opcodes[1] = {
		type: 4,
		index: 21
	}, this.rules[19].opcodes[2] = {
		type: 7,
		string: [58]
	}, this.rules[19].opcodes[3] = {
		type: 4,
		index: 20
	}, this.rules[19].opcodes[4] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[19].opcodes[5] = {
		type: 2,
		children: [6, 7]
	}, this.rules[19].opcodes[6] = {
		type: 7,
		string: [63]
	}, this.rules[19].opcodes[7] = {
		type: 4,
		index: 45
	}, this.rules[19].opcodes[8] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[19].opcodes[9] = {
		type: 2,
		children: [10, 11]
	}, this.rules[19].opcodes[10] = {
		type: 7,
		string: [35]
	}, this.rules[19].opcodes[11] = {
		type: 4,
		index: 46
	}, this.rules[20].opcodes = [], this.rules[20].opcodes[0] = {
		type: 1,
		children: [
			1,
			5,
			6,
			7
		]
	}, this.rules[20].opcodes[1] = {
		type: 2,
		children: [
			2,
			3,
			4
		]
	}, this.rules[20].opcodes[2] = {
		type: 7,
		string: [47, 47]
	}, this.rules[20].opcodes[3] = {
		type: 4,
		index: 22
	}, this.rules[20].opcodes[4] = {
		type: 4,
		index: 23
	}, this.rules[20].opcodes[5] = {
		type: 4,
		index: 24
	}, this.rules[20].opcodes[6] = {
		type: 4,
		index: 25
	}, this.rules[20].opcodes[7] = {
		type: 4,
		index: 26
	}, this.rules[21].opcodes = [], this.rules[21].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[21].opcodes[1] = {
		type: 4,
		index: 77
	}, this.rules[21].opcodes[2] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[21].opcodes[3] = {
		type: 1,
		children: [
			4,
			5,
			6,
			7
		]
	}, this.rules[21].opcodes[4] = {
		type: 4,
		index: 77
	}, this.rules[21].opcodes[5] = {
		type: 4,
		index: 79
	}, this.rules[21].opcodes[6] = {
		type: 6,
		string: [43]
	}, this.rules[21].opcodes[7] = {
		type: 5,
		min: 45,
		max: 46
	}, this.rules[22].opcodes = [], this.rules[22].opcodes[0] = {
		type: 2,
		children: [
			1,
			3,
			4
		]
	}, this.rules[22].opcodes[1] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[22].opcodes[2] = {
		type: 4,
		index: 27
	}, this.rules[22].opcodes[3] = {
		type: 4,
		index: 29
	}, this.rules[22].opcodes[4] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[22].opcodes[5] = {
		type: 2,
		children: [6, 7]
	}, this.rules[22].opcodes[6] = {
		type: 7,
		string: [58]
	}, this.rules[22].opcodes[7] = {
		type: 4,
		index: 44
	}, this.rules[23].opcodes = [], this.rules[23].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[23].opcodes[1] = {
		type: 2,
		children: [2, 3]
	}, this.rules[23].opcodes[2] = {
		type: 7,
		string: [47]
	}, this.rules[23].opcodes[3] = {
		type: 4,
		index: 60
	}, this.rules[24].opcodes = [], this.rules[24].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[24].opcodes[1] = {
		type: 7,
		string: [47]
	}, this.rules[24].opcodes[2] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[24].opcodes[3] = {
		type: 2,
		children: [4, 5]
	}, this.rules[24].opcodes[4] = {
		type: 4,
		index: 61
	}, this.rules[24].opcodes[5] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[24].opcodes[6] = {
		type: 2,
		children: [7, 8]
	}, this.rules[24].opcodes[7] = {
		type: 7,
		string: [47]
	}, this.rules[24].opcodes[8] = {
		type: 4,
		index: 60
	}, this.rules[25].opcodes = [], this.rules[25].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[25].opcodes[1] = {
		type: 4,
		index: 61
	}, this.rules[25].opcodes[2] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[25].opcodes[3] = {
		type: 2,
		children: [4, 5]
	}, this.rules[25].opcodes[4] = {
		type: 7,
		string: [47]
	}, this.rules[25].opcodes[5] = {
		type: 4,
		index: 60
	}, this.rules[26].opcodes = [], this.rules[26].opcodes[0] = {
		type: 7,
		string: []
	}, this.rules[27].opcodes = [], this.rules[27].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[27].opcodes[1] = {
		type: 4,
		index: 28
	}, this.rules[27].opcodes[2] = {
		type: 6,
		string: [64]
	}, this.rules[28].opcodes = [], this.rules[28].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[28].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4,
			5,
			6,
			7,
			8,
			9,
			10,
			11,
			12
		]
	}, this.rules[28].opcodes[2] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[28].opcodes[3] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[28].opcodes[4] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[28].opcodes[5] = {
		type: 4,
		index: 63
	}, this.rules[28].opcodes[6] = {
		type: 6,
		string: [33]
	}, this.rules[28].opcodes[7] = {
		type: 6,
		string: [36]
	}, this.rules[28].opcodes[8] = {
		type: 5,
		min: 38,
		max: 46
	}, this.rules[28].opcodes[9] = {
		type: 5,
		min: 58,
		max: 59
	}, this.rules[28].opcodes[10] = {
		type: 6,
		string: [61]
	}, this.rules[28].opcodes[11] = {
		type: 6,
		string: [95]
	}, this.rules[28].opcodes[12] = {
		type: 6,
		string: [126]
	}, this.rules[29].opcodes = [], this.rules[29].opcodes[0] = {
		type: 1,
		children: [
			1,
			2,
			6
		]
	}, this.rules[29].opcodes[1] = {
		type: 4,
		index: 30
	}, this.rules[29].opcodes[2] = {
		type: 2,
		children: [3, 4]
	}, this.rules[29].opcodes[3] = {
		type: 4,
		index: 39
	}, this.rules[29].opcodes[4] = { type: 13 }, this.rules[29].opcodes[5] = {
		type: 4,
		index: 43
	}, this.rules[29].opcodes[6] = {
		type: 4,
		index: 42
	}, this.rules[30].opcodes = [], this.rules[30].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			5
		]
	}, this.rules[30].opcodes[1] = {
		type: 7,
		string: [91]
	}, this.rules[30].opcodes[2] = {
		type: 1,
		children: [3, 4]
	}, this.rules[30].opcodes[3] = {
		type: 4,
		index: 32
	}, this.rules[30].opcodes[4] = {
		type: 4,
		index: 31
	}, this.rules[30].opcodes[5] = {
		type: 7,
		string: [93]
	}, this.rules[31].opcodes = [], this.rules[31].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			4,
			5
		]
	}, this.rules[31].opcodes[1] = {
		type: 7,
		string: [118]
	}, this.rules[31].opcodes[2] = {
		type: 3,
		min: 1,
		max: Infinity
	}, this.rules[31].opcodes[3] = {
		type: 4,
		index: 80
	}, this.rules[31].opcodes[4] = {
		type: 7,
		string: [46]
	}, this.rules[31].opcodes[5] = {
		type: 3,
		min: 1,
		max: Infinity
	}, this.rules[31].opcodes[6] = {
		type: 1,
		children: [
			7,
			8,
			9,
			10,
			11,
			12,
			13,
			14,
			15,
			16
		]
	}, this.rules[31].opcodes[7] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[31].opcodes[8] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[31].opcodes[9] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[31].opcodes[10] = {
		type: 6,
		string: [33]
	}, this.rules[31].opcodes[11] = {
		type: 6,
		string: [36]
	}, this.rules[31].opcodes[12] = {
		type: 5,
		min: 38,
		max: 46
	}, this.rules[31].opcodes[13] = {
		type: 5,
		min: 58,
		max: 59
	}, this.rules[31].opcodes[14] = {
		type: 6,
		string: [61]
	}, this.rules[31].opcodes[15] = {
		type: 6,
		string: [95]
	}, this.rules[31].opcodes[16] = {
		type: 6,
		string: [126]
	}, this.rules[32].opcodes = [], this.rules[32].opcodes[0] = {
		type: 1,
		children: [1, 2]
	}, this.rules[32].opcodes[1] = {
		type: 4,
		index: 33
	}, this.rules[32].opcodes[2] = {
		type: 4,
		index: 34
	}, this.rules[33].opcodes = [], this.rules[33].opcodes[0] = {
		type: 2,
		children: [1, 5]
	}, this.rules[33].opcodes[1] = {
		type: 2,
		children: [2, 3]
	}, this.rules[33].opcodes[2] = {
		type: 4,
		index: 37
	}, this.rules[33].opcodes[3] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[33].opcodes[4] = {
		type: 4,
		index: 38
	}, this.rules[33].opcodes[5] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[33].opcodes[6] = {
		type: 2,
		children: [7, 8]
	}, this.rules[33].opcodes[7] = {
		type: 6,
		string: [58]
	}, this.rules[33].opcodes[8] = {
		type: 4,
		index: 39
	}, this.rules[34].opcodes = [], this.rules[34].opcodes[0] = {
		type: 2,
		children: [
			1,
			6,
			7
		]
	}, this.rules[34].opcodes[1] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[34].opcodes[2] = {
		type: 2,
		children: [3, 4]
	}, this.rules[34].opcodes[3] = {
		type: 4,
		index: 35
	}, this.rules[34].opcodes[4] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[34].opcodes[5] = {
		type: 4,
		index: 36
	}, this.rules[34].opcodes[6] = {
		type: 6,
		string: [58, 58]
	}, this.rules[34].opcodes[7] = {
		type: 1,
		children: [8, 17]
	}, this.rules[34].opcodes[8] = {
		type: 2,
		children: [9, 13]
	}, this.rules[34].opcodes[9] = {
		type: 2,
		children: [10, 11]
	}, this.rules[34].opcodes[10] = {
		type: 4,
		index: 37
	}, this.rules[34].opcodes[11] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[34].opcodes[12] = {
		type: 4,
		index: 38
	}, this.rules[34].opcodes[13] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[34].opcodes[14] = {
		type: 2,
		children: [15, 16]
	}, this.rules[34].opcodes[15] = {
		type: 6,
		string: [58]
	}, this.rules[34].opcodes[16] = {
		type: 4,
		index: 39
	}, this.rules[34].opcodes[17] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[34].opcodes[18] = {
		type: 4,
		index: 39
	}, this.rules[35].opcodes = [], this.rules[35].opcodes[0] = {
		type: 3,
		min: 1,
		max: 4
	}, this.rules[35].opcodes[1] = {
		type: 4,
		index: 80
	}, this.rules[36].opcodes = [], this.rules[36].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[36].opcodes[1] = {
		type: 6,
		string: [58]
	}, this.rules[36].opcodes[2] = {
		type: 3,
		min: 1,
		max: 4
	}, this.rules[36].opcodes[3] = {
		type: 4,
		index: 80
	}, this.rules[37].opcodes = [], this.rules[37].opcodes[0] = {
		type: 2,
		children: [1, 3]
	}, this.rules[37].opcodes[1] = {
		type: 3,
		min: 1,
		max: 4
	}, this.rules[37].opcodes[2] = {
		type: 4,
		index: 80
	}, this.rules[37].opcodes[3] = { type: 13 }, this.rules[37].opcodes[4] = {
		type: 6,
		string: [46]
	}, this.rules[38].opcodes = [], this.rules[38].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			4
		]
	}, this.rules[38].opcodes[1] = {
		type: 6,
		string: [58]
	}, this.rules[38].opcodes[2] = {
		type: 3,
		min: 1,
		max: 4
	}, this.rules[38].opcodes[3] = {
		type: 4,
		index: 80
	}, this.rules[38].opcodes[4] = { type: 13 }, this.rules[38].opcodes[5] = {
		type: 6,
		string: [46]
	}, this.rules[39].opcodes = [], this.rules[39].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3,
			4,
			5,
			6,
			7
		]
	}, this.rules[39].opcodes[1] = {
		type: 4,
		index: 40
	}, this.rules[39].opcodes[2] = {
		type: 7,
		string: [46]
	}, this.rules[39].opcodes[3] = {
		type: 4,
		index: 40
	}, this.rules[39].opcodes[4] = {
		type: 7,
		string: [46]
	}, this.rules[39].opcodes[5] = {
		type: 4,
		index: 40
	}, this.rules[39].opcodes[6] = {
		type: 7,
		string: [46]
	}, this.rules[39].opcodes[7] = {
		type: 4,
		index: 40
	}, this.rules[40].opcodes = [], this.rules[40].opcodes[0] = {
		type: 3,
		min: 1,
		max: 3
	}, this.rules[40].opcodes[1] = {
		type: 4,
		index: 41
	}, this.rules[41].opcodes = [], this.rules[41].opcodes[0] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[42].opcodes = [], this.rules[42].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[42].opcodes[1] = {
		type: 4,
		index: 43
	}, this.rules[43].opcodes = [], this.rules[43].opcodes[0] = {
		type: 1,
		children: [
			1,
			2,
			3,
			4,
			5,
			6,
			7,
			8,
			9,
			10,
			11
		]
	}, this.rules[43].opcodes[1] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[43].opcodes[2] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[43].opcodes[3] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[43].opcodes[4] = {
		type: 4,
		index: 63
	}, this.rules[43].opcodes[5] = {
		type: 6,
		string: [33]
	}, this.rules[43].opcodes[6] = {
		type: 6,
		string: [36]
	}, this.rules[43].opcodes[7] = {
		type: 5,
		min: 38,
		max: 46
	}, this.rules[43].opcodes[8] = {
		type: 6,
		string: [59]
	}, this.rules[43].opcodes[9] = {
		type: 6,
		string: [61]
	}, this.rules[43].opcodes[10] = {
		type: 6,
		string: [95]
	}, this.rules[43].opcodes[11] = {
		type: 6,
		string: [126]
	}, this.rules[44].opcodes = [], this.rules[44].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[44].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[45].opcodes = [], this.rules[45].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[45].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4
		]
	}, this.rules[45].opcodes[2] = {
		type: 4,
		index: 62
	}, this.rules[45].opcodes[3] = {
		type: 6,
		string: [47]
	}, this.rules[45].opcodes[4] = {
		type: 6,
		string: [63]
	}, this.rules[46].opcodes = [], this.rules[46].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[46].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4
		]
	}, this.rules[46].opcodes[2] = {
		type: 4,
		index: 62
	}, this.rules[46].opcodes[3] = {
		type: 6,
		string: [47]
	}, this.rules[46].opcodes[4] = {
		type: 6,
		string: [63]
	}, this.rules[47].opcodes = [], this.rules[47].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3,
			4,
			8
		]
	}, this.rules[47].opcodes[1] = {
		type: 4,
		index: 49
	}, this.rules[47].opcodes[2] = {
		type: 7,
		string: [58]
	}, this.rules[47].opcodes[3] = {
		type: 4,
		index: 48
	}, this.rules[47].opcodes[4] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[47].opcodes[5] = {
		type: 2,
		children: [6, 7]
	}, this.rules[47].opcodes[6] = {
		type: 7,
		string: [63]
	}, this.rules[47].opcodes[7] = {
		type: 4,
		index: 50
	}, this.rules[47].opcodes[8] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[47].opcodes[9] = {
		type: 2,
		children: [10, 11]
	}, this.rules[47].opcodes[10] = {
		type: 7,
		string: [35]
	}, this.rules[47].opcodes[11] = {
		type: 4,
		index: 51
	}, this.rules[48].opcodes = [], this.rules[48].opcodes[0] = {
		type: 1,
		children: [
			1,
			5,
			6,
			7
		]
	}, this.rules[48].opcodes[1] = {
		type: 2,
		children: [
			2,
			3,
			4
		]
	}, this.rules[48].opcodes[2] = {
		type: 7,
		string: [47, 47]
	}, this.rules[48].opcodes[3] = {
		type: 4,
		index: 52
	}, this.rules[48].opcodes[4] = {
		type: 4,
		index: 56
	}, this.rules[48].opcodes[5] = {
		type: 4,
		index: 57
	}, this.rules[48].opcodes[6] = {
		type: 4,
		index: 58
	}, this.rules[48].opcodes[7] = {
		type: 4,
		index: 59
	}, this.rules[49].opcodes = [], this.rules[49].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[49].opcodes[1] = {
		type: 4,
		index: 77
	}, this.rules[49].opcodes[2] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[49].opcodes[3] = {
		type: 1,
		children: [
			4,
			5,
			6,
			7
		]
	}, this.rules[49].opcodes[4] = {
		type: 4,
		index: 77
	}, this.rules[49].opcodes[5] = {
		type: 4,
		index: 79
	}, this.rules[49].opcodes[6] = {
		type: 6,
		string: [43]
	}, this.rules[49].opcodes[7] = {
		type: 5,
		min: 45,
		max: 46
	}, this.rules[50].opcodes = [], this.rules[50].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[50].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4
		]
	}, this.rules[50].opcodes[2] = {
		type: 4,
		index: 62
	}, this.rules[50].opcodes[3] = {
		type: 6,
		string: [47]
	}, this.rules[50].opcodes[4] = {
		type: 6,
		string: [63]
	}, this.rules[51].opcodes = [], this.rules[51].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[51].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4
		]
	}, this.rules[51].opcodes[2] = {
		type: 4,
		index: 62
	}, this.rules[51].opcodes[3] = {
		type: 6,
		string: [47]
	}, this.rules[51].opcodes[4] = {
		type: 6,
		string: [63]
	}, this.rules[52].opcodes = [], this.rules[52].opcodes[0] = {
		type: 2,
		children: [
			1,
			5,
			6
		]
	}, this.rules[52].opcodes[1] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[52].opcodes[2] = {
		type: 2,
		children: [3, 4]
	}, this.rules[52].opcodes[3] = {
		type: 4,
		index: 53
	}, this.rules[52].opcodes[4] = {
		type: 6,
		string: [64]
	}, this.rules[52].opcodes[5] = {
		type: 4,
		index: 54
	}, this.rules[52].opcodes[6] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[52].opcodes[7] = {
		type: 2,
		children: [8, 9]
	}, this.rules[52].opcodes[8] = {
		type: 7,
		string: [58]
	}, this.rules[52].opcodes[9] = {
		type: 4,
		index: 55
	}, this.rules[53].opcodes = [], this.rules[53].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[53].opcodes[1] = {
		type: 1,
		children: [
			2,
			3,
			4,
			5,
			6,
			7,
			8,
			9,
			10,
			11,
			12
		]
	}, this.rules[53].opcodes[2] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[53].opcodes[3] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[53].opcodes[4] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[53].opcodes[5] = {
		type: 4,
		index: 63
	}, this.rules[53].opcodes[6] = {
		type: 6,
		string: [33]
	}, this.rules[53].opcodes[7] = {
		type: 6,
		string: [36]
	}, this.rules[53].opcodes[8] = {
		type: 5,
		min: 38,
		max: 46
	}, this.rules[53].opcodes[9] = {
		type: 5,
		min: 58,
		max: 59
	}, this.rules[53].opcodes[10] = {
		type: 6,
		string: [61]
	}, this.rules[53].opcodes[11] = {
		type: 6,
		string: [95]
	}, this.rules[53].opcodes[12] = {
		type: 6,
		string: [126]
	}, this.rules[54].opcodes = [], this.rules[54].opcodes[0] = {
		type: 1,
		children: [
			1,
			2,
			6
		]
	}, this.rules[54].opcodes[1] = {
		type: 4,
		index: 30
	}, this.rules[54].opcodes[2] = {
		type: 2,
		children: [3, 4]
	}, this.rules[54].opcodes[3] = {
		type: 4,
		index: 39
	}, this.rules[54].opcodes[4] = { type: 13 }, this.rules[54].opcodes[5] = {
		type: 4,
		index: 43
	}, this.rules[54].opcodes[6] = {
		type: 4,
		index: 42
	}, this.rules[55].opcodes = [], this.rules[55].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[55].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[56].opcodes = [], this.rules[56].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[56].opcodes[1] = {
		type: 2,
		children: [2, 3]
	}, this.rules[56].opcodes[2] = {
		type: 7,
		string: [47]
	}, this.rules[56].opcodes[3] = {
		type: 4,
		index: 60
	}, this.rules[57].opcodes = [], this.rules[57].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[57].opcodes[1] = {
		type: 7,
		string: [47]
	}, this.rules[57].opcodes[2] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[57].opcodes[3] = {
		type: 2,
		children: [4, 5]
	}, this.rules[57].opcodes[4] = {
		type: 4,
		index: 61
	}, this.rules[57].opcodes[5] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[57].opcodes[6] = {
		type: 2,
		children: [7, 8]
	}, this.rules[57].opcodes[7] = {
		type: 7,
		string: [47]
	}, this.rules[57].opcodes[8] = {
		type: 4,
		index: 60
	}, this.rules[58].opcodes = [], this.rules[58].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[58].opcodes[1] = {
		type: 4,
		index: 61
	}, this.rules[58].opcodes[2] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[58].opcodes[3] = {
		type: 2,
		children: [4, 5]
	}, this.rules[58].opcodes[4] = {
		type: 7,
		string: [47]
	}, this.rules[58].opcodes[5] = {
		type: 4,
		index: 60
	}, this.rules[59].opcodes = [], this.rules[59].opcodes[0] = {
		type: 7,
		string: []
	}, this.rules[60].opcodes = [], this.rules[60].opcodes[0] = {
		type: 3,
		min: 0,
		max: Infinity
	}, this.rules[60].opcodes[1] = {
		type: 4,
		index: 62
	}, this.rules[61].opcodes = [], this.rules[61].opcodes[0] = {
		type: 3,
		min: 1,
		max: Infinity
	}, this.rules[61].opcodes[1] = {
		type: 4,
		index: 62
	}, this.rules[62].opcodes = [], this.rules[62].opcodes[0] = {
		type: 1,
		children: [
			1,
			2,
			3,
			4,
			5,
			6,
			7,
			8,
			9,
			10,
			11,
			12
		]
	}, this.rules[62].opcodes[1] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[62].opcodes[2] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[62].opcodes[3] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[62].opcodes[4] = {
		type: 4,
		index: 63
	}, this.rules[62].opcodes[5] = {
		type: 6,
		string: [33]
	}, this.rules[62].opcodes[6] = {
		type: 6,
		string: [36]
	}, this.rules[62].opcodes[7] = {
		type: 5,
		min: 38,
		max: 46
	}, this.rules[62].opcodes[8] = {
		type: 5,
		min: 58,
		max: 59
	}, this.rules[62].opcodes[9] = {
		type: 6,
		string: [61]
	}, this.rules[62].opcodes[10] = {
		type: 6,
		string: [64]
	}, this.rules[62].opcodes[11] = {
		type: 6,
		string: [95]
	}, this.rules[62].opcodes[12] = {
		type: 6,
		string: [126]
	}, this.rules[63].opcodes = [], this.rules[63].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3
		]
	}, this.rules[63].opcodes[1] = {
		type: 6,
		string: [37]
	}, this.rules[63].opcodes[2] = {
		type: 4,
		index: 80
	}, this.rules[63].opcodes[3] = {
		type: 4,
		index: 80
	}, this.rules[64].opcodes = [], this.rules[64].opcodes[0] = {
		type: 3,
		min: 4,
		max: 4
	}, this.rules[64].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[65].opcodes = [], this.rules[65].opcodes[0] = {
		type: 3,
		min: 2,
		max: 2
	}, this.rules[65].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[66].opcodes = [], this.rules[66].opcodes[0] = {
		type: 3,
		min: 2,
		max: 2
	}, this.rules[66].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[67].opcodes = [], this.rules[67].opcodes[0] = {
		type: 3,
		min: 2,
		max: 2
	}, this.rules[67].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[68].opcodes = [], this.rules[68].opcodes[0] = {
		type: 3,
		min: 2,
		max: 2
	}, this.rules[68].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[69].opcodes = [], this.rules[69].opcodes[0] = {
		type: 3,
		min: 2,
		max: 2
	}, this.rules[69].opcodes[1] = {
		type: 4,
		index: 79
	}, this.rules[70].opcodes = [], this.rules[70].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[70].opcodes[1] = {
		type: 7,
		string: [46]
	}, this.rules[70].opcodes[2] = {
		type: 3,
		min: 1,
		max: Infinity
	}, this.rules[70].opcodes[3] = {
		type: 4,
		index: 79
	}, this.rules[71].opcodes = [], this.rules[71].opcodes[0] = {
		type: 2,
		children: [
			1,
			4,
			5,
			6
		]
	}, this.rules[71].opcodes[1] = {
		type: 1,
		children: [2, 3]
	}, this.rules[71].opcodes[2] = {
		type: 7,
		string: [43]
	}, this.rules[71].opcodes[3] = {
		type: 7,
		string: [45]
	}, this.rules[71].opcodes[4] = {
		type: 4,
		index: 67
	}, this.rules[71].opcodes[5] = {
		type: 7,
		string: [58]
	}, this.rules[71].opcodes[6] = {
		type: 4,
		index: 68
	}, this.rules[72].opcodes = [], this.rules[72].opcodes[0] = {
		type: 1,
		children: [1, 2]
	}, this.rules[72].opcodes[1] = {
		type: 7,
		string: [122]
	}, this.rules[72].opcodes[2] = {
		type: 4,
		index: 71
	}, this.rules[73].opcodes = [], this.rules[73].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3,
			4,
			5,
			6
		]
	}, this.rules[73].opcodes[1] = {
		type: 4,
		index: 67
	}, this.rules[73].opcodes[2] = {
		type: 7,
		string: [58]
	}, this.rules[73].opcodes[3] = {
		type: 4,
		index: 68
	}, this.rules[73].opcodes[4] = {
		type: 7,
		string: [58]
	}, this.rules[73].opcodes[5] = {
		type: 4,
		index: 69
	}, this.rules[73].opcodes[6] = {
		type: 3,
		min: 0,
		max: 1
	}, this.rules[73].opcodes[7] = {
		type: 4,
		index: 70
	}, this.rules[74].opcodes = [], this.rules[74].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3,
			4,
			5
		]
	}, this.rules[74].opcodes[1] = {
		type: 4,
		index: 64
	}, this.rules[74].opcodes[2] = {
		type: 7,
		string: [45]
	}, this.rules[74].opcodes[3] = {
		type: 4,
		index: 65
	}, this.rules[74].opcodes[4] = {
		type: 7,
		string: [45]
	}, this.rules[74].opcodes[5] = {
		type: 4,
		index: 66
	}, this.rules[75].opcodes = [], this.rules[75].opcodes[0] = {
		type: 2,
		children: [1, 2]
	}, this.rules[75].opcodes[1] = {
		type: 4,
		index: 73
	}, this.rules[75].opcodes[2] = {
		type: 4,
		index: 72
	}, this.rules[76].opcodes = [], this.rules[76].opcodes[0] = {
		type: 2,
		children: [
			1,
			2,
			3
		]
	}, this.rules[76].opcodes[1] = {
		type: 4,
		index: 74
	}, this.rules[76].opcodes[2] = {
		type: 7,
		string: [116]
	}, this.rules[76].opcodes[3] = {
		type: 4,
		index: 75
	}, this.rules[77].opcodes = [], this.rules[77].opcodes[0] = {
		type: 1,
		children: [1, 2]
	}, this.rules[77].opcodes[1] = {
		type: 5,
		min: 65,
		max: 90
	}, this.rules[77].opcodes[2] = {
		type: 5,
		min: 97,
		max: 122
	}, this.rules[78].opcodes = [], this.rules[78].opcodes[0] = {
		type: 6,
		string: [10]
	}, this.rules[79].opcodes = [], this.rules[79].opcodes[0] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[80].opcodes = [], this.rules[80].opcodes[0] = {
		type: 1,
		children: [
			1,
			2,
			3
		]
	}, this.rules[80].opcodes[1] = {
		type: 5,
		min: 48,
		max: 57
	}, this.rules[80].opcodes[2] = {
		type: 5,
		min: 65,
		max: 70
	}, this.rules[80].opcodes[3] = {
		type: 5,
		min: 97,
		max: 102
	}, this.toString = function() {
		let e = "";
		return e += "; LDT 05/06/2024 \r\n", e += "; modified in several significant ways\r\n", e += "; 1) Literal strings are replaced with numbers and ranges (%d32 & %d32-126, etc.) when possible.\r\n", e += ";    TRB and especially TRG operators are much more efficient than TLS operators.\r\n", e += "; 2) Two rules, authority and URI, are used multiple times in different contexts. These rules will be reproduced and renamed\r\n", e += ";    in order to a) recognize the context and b) remove unneccary callback functions for certain contexts.\r\n", e += ";    This will simiplify recognizing contexts AND remove unneccesary callbacks\r\n", e += "; 2.a) domain is defined as authority-d which is identical to authority except that there will be no\r\n", e += ";      callback functions defined on authority-d or any of its *-d components.\r\n", e += "; 2.b) The resource URI is defined as URI-r and its components defined as *-r.\r\n", e += ";      In this way, callback functions can be defined on URI and is components while\r\n", e += ";      leaving URI-r to be parsed identically with no unnecessary callback functions to slow it down.\r\n", e += "; 3) IPv6address does not work because of APG's \"first-success disambiguation\" and \"greedy\" repetitions.\r\n", e += ";    IPv6address redefined and validations moved to callback functions (semantic vs syntactic validation)\r\n", e += ";    Redefinition requires negative look-ahead operators, https://en.wikipedia.org/wiki/Syntactic_predicate\r\n", e += ";    That is SABNF instead of simple ABNF.\r\n", e += "; 4) IPv4address fails because of \"first-success disambiguation\".\r\n", e += ";    This could be fixed with rearrangement of the alternative terms. However, it would still not\r\n", e += ";    accept zero-padded (leading zeros) decimal octets.\r\n", e += ";    Therefore, IPv4address is also done with callback functions and semantic validation.\r\n", e += "; 5) The negative look-ahead operator is also needed in the definition of host to\r\n", e += ";    prevent failure with a reg-name that begins with an IPv4 address.\r\n", e += "; 6) NOTE: host = 1.1.1.256 is a valid host name even though it is an invalid IPv4address.\r\n", e += ";          The IPv4address alternative fails but the reg-name alternative succeeds.\r\n", e += "; 7) The Ethereum spec (https://eips.ethereum.org/EIPS/eip-4361) message format ABNF\r\n", e += ";    allows for empty statements. Because of the \"first success disambiguation\" of APG\r\n", e += ";    the an explicit \"empty-statement\" rule is required to match the spec's intent.\r\n", e += "\r\n", e += "\r\n", e += "sign-in-with-ethereum =\r\n", e += "    oscheme domain %s\" wants you to sign in with your Ethereum account:\" LF\r\n", e += "    address LF\r\n", e += "    ((LF statement LF LF) / empty-statement / (LF LF))\r\n", e += "    %s\"URI: \" URI LF\r\n", e += "    %s\"Version: \" version LF\r\n", e += "    %s\"Chain ID: \" chain-id LF\r\n", e += "    %s\"Nonce: \" nonce LF\r\n", e += "    %s\"Issued At: \" issued-at\r\n", e += "    [ LF ex-title expiration-time ]\r\n", e += "    [ LF nb-title not-before ]\r\n", e += "    [ LF ri-title request-id ]\r\n", e += "    [ LF re-title resources ]\r\n", e += "ex-title        = %s\"Expiration Time: \"\r\n", e += "nb-title        = %s\"Not Before: \"\r\n", e += "ri-title        = %s\"Request ID: \"\r\n", e += "re-title        = %s\"Resources:\"\r\n", e += "oscheme         = [ ALPHA *( ALPHA / DIGIT / %d43 / %d45-46 ) \"://\" ]\r\n", e += "domain          = authority-d\r\n", e += "address         = \"0x\" 40*40HEXDIG\r\n", e += "    ; Must also conform to captilization\r\n", e += "    ; checksum encoding specified in EIP-55\r\n", e += "    ; where applicable (EOAs).\r\n", e += "\r\n", e += "statement       = 1*( %d97-122 / %d65-90 / %d48-57 / %d32-33 / %d35-36 / %d38-59 / %d61 / %d63-64 / %d91 / %d93 / %d95 / %d126)\r\n", e += "    ; The purpose is to exclude LF (line breaks).\r\n", e += "    ; LDT 10/04/2023: Do you mean %d32-126? All printing characters\r\n", e += "empty-statement = LF LF LF\r\n", e += "version         = \"1\"\r\n", e += "nonce           = 8*( ALPHA / DIGIT )\r\n", e += "issued-at       = date-time\r\n", e += "expiration-time = date-time\r\n", e += "not-before      = date-time\r\n", e += "request-id      = *pchar\r\n", e += "chain-id        = 1*DIGIT\r\n", e += "    ; See EIP-155 for valid CHAIN_IDs.\r\n", e += "resources       = *( LF resource )\r\n", e += "resource        = \"- \" URI-r\r\n", e += "\r\n", e += "; ------------------------------------------------------------------------------\r\n", e += "; RFC 3986\r\n", e += "\r\n", e += "URI           = scheme \":\" hier-part [ \"?\" query ] [ \"#\" fragment ]\r\n", e += "hier-part     = \"//\" authority path-abempty\r\n", e += "              / path-absolute\r\n", e += "              / path-rootless\r\n", e += "              / path-empty\r\n", e += "scheme        = ALPHA *( ALPHA / DIGIT / %d43 / %d45-46 )\r\n", e += "authority     = [ userinfo-at ] host [ \":\" port ]\r\n", e += "path-abempty  = *( \"/\" segment )\r\n", e += "path-absolute = \"/\" [ segment-nz *( \"/\" segment ) ]\r\n", e += "path-rootless = segment-nz *( \"/\" segment )\r\n", e += "path-empty    = \"\"\r\n", e += "userinfo-at   = userinfo %d64\r\n", e += "                ; userinfo redefined to include the \"@\" so that it will fail without it\r\n", e += "                ; otherwise userinfo can match host and then the parser will backtrack\r\n", e += "                ; incorrectly keeping the captured userinfo phrase\r\n", e += "userinfo      = *(%d97-122 / %d65-90 / %d48-57 / pct-encoded / %d33 / %d36 / %d38-46 / %d58-59 / %d61 / %d95 / %d126)\r\n", e += "host          = IP-literal / (IPv4address !reg-name-char) / reg-name\r\n", e += "                ; negative look-ahead required to prevent IPv4address from being recognized as first part of reg-name\r\n", e += "                ; same fix as https://github.com/garycourt/uri-js/issues/4\r\n", e += "IP-literal    = \"[\" ( IPv6address / IPvFuture  ) \"]\"\r\n", e += "IPvFuture     = \"v\" 1*HEXDIG \".\" 1*( %d97-122 / %d65-90 / %d48-57 / %d33 / %d36 /%d38-46 / %d58-59 /%d61 /%d95 / %d126 )\r\n", e += "IPv6address   = nodcolon / dcolon\r\n", e += "nodcolon      = (h16n *h16cn) [%d58 IPv4address]\r\n", e += "dcolon        = [h16 *h16c] %d58.58 (((h16n *h16cn) [%d58 IPv4address]) / [IPv4address])\r\n", e += "h16           = 1*4HEXDIG\r\n", e += "h16c          = %d58 1*4HEXDIG\r\n", e += "h16n          = 1*4HEXDIG !%d46\r\n", e += "h16cn         = %d58 1*4HEXDIG !%d46\r\n", e += "IPv4address   = dec-octet \".\" dec-octet \".\" dec-octet \".\" dec-octet\r\n", e += "; Here we will will use callback functions to evaluate and validate the (possibly zero-padded) dec-octet.\r\n", e += "dec-octet     =  1*3dec-digit\r\n", e += "dec-digit     = %d48-57\r\n", e += "reg-name      = *reg-name-char\r\n", e += "reg-name-char = %d97-122 / %d65-90 / %d48-57 / pct-encoded / %d33 / %d36 / %d38-46 / %d59 / %d61 /%d95 / %d126\r\n", e += "port          = *DIGIT\r\n", e += "query         = *(pchar / %d47 / %d63)\r\n", e += "fragment      = *(pchar / %d47 / %d63)\r\n", e += "\r\n", e += "; URI-r is a redefiniton of URI but without the callback functions attached to it\r\n", e += "; it reuses athority-d from domain \r\n", e += "URI-r         = scheme-r \":\" hier-part-r [ \"?\" query-r ] [ \"#\" fragment-r ]\r\n", e += "hier-part-r   = \"//\" authority-d path-abempty-r\r\n", e += "              / path-absolute-r\r\n", e += "              / path-rootless-r\r\n", e += "              / path-empty-r\r\n", e += "scheme-r      = ALPHA *( ALPHA / DIGIT / %d43 / %d45-46 )\r\n", e += "query-r       = *(pchar / %d47 / %d63)\r\n", e += "fragment-r    = *(pchar / %d47 / %d63)\r\n", e += "\r\n", e += "; authority-d is a redefinition of authority for capturing the domian phrase\r\n", e += "; but without callback functions \r\n", e += "; it is reused for URI- for the same reason               \r\n", e += "authority-d   = [ userinfo-d %d64 ] host-d [ \":\" port-d ]\r\n", e += "userinfo-d    = *(%d97-122 / %d65-90 / %d48-57 / pct-encoded / %d33 / %d36 / %d38-46 / %d58-59 / %d61 / %d95 / %d126)\r\n", e += "host-d        = IP-literal / (IPv4address !reg-name-char) / reg-name\r\n", e += "port-d        = *DIGIT\r\n", e += "\r\n", e += "; for use with URI-r\r\n", e += "path-abempty-r  = *( \"/\" segment )\r\n", e += "path-absolute-r = \"/\" [ segment-nz *( \"/\" segment ) ]\r\n", e += "path-rootless-r = segment-nz *( \"/\" segment )\r\n", e += "path-empty-r    = \"\"\r\n", e += "segment       = *pchar\r\n", e += "segment-nz    = 1*pchar\r\n", e += "pchar         = (%d97-122 / %d65-90 / %d48-57 / pct-encoded / %d33 / %d36 / %d38-46 /%d58-59 / %d61 / %d64 / %d95 / %d126)\r\n", e += "pct-encoded   = %d37 HEXDIG HEXDIG\r\n", e += "\r\n", e += "; no longer needed - expanded for all usage for fewer branches in the parse there\r\n", e += "; and more efficient use of the TBS & TRG operators in place of TLS and rule names\r\n", e += "; does not work with APG probably because of \"first-success disambiguation\" and greedy repetitions.\r\n", e += "; will replace with semantic checking of valid number of h16s\r\n", e += ";IPv6address   =                            6( h16 \":\" ) ls32\r\n", e += ";              /                       \"::\" 5( h16 \":\" ) ls32\r\n", e += ";              / [               h16 ] \"::\" 4( h16 \":\" ) ls32\r\n", e += ";              / [ *1( h16 \":\" ) h16 ] \"::\" 3( h16 \":\" ) ls32\r\n", e += ";              / [ *2( h16 \":\" ) h16 ] \"::\" 2( h16 \":\" ) ls32\r\n", e += ";              / [ *3( h16 \":\" ) h16 ] \"::\"    h16 \":\"   ls32\r\n", e += ";              / [ *4( h16 \":\" ) h16 ] \"::\"              ls32\r\n", e += ";              / [ *5( h16 \":\" ) h16 ] \"::\"              h16\r\n", e += ";              / [ *6( h16 \":\" ) h16 ] \"::\"\r\n", e += ";ls32          = ( h16 \":\" h16 ) / IPv4address\r\n", e += "; dec-octet does not work because of \"first-success disambiguation\".\r\n", e += "; Must have the longest (3-digit) numbers first.\r\n", e += "; Even so, this form does not accept leading zeros.\r\n", e += "; There does not seem to be a clear standard for this (https://en.wikipedia.org/wiki/Dot-decimal_notation)\r\n", e += "; however and early RFC 790 did show leading-zero padding of the three digits.\r\n", e += ";dec-octet     = DIGIT                 ; 0-9\r\n", e += ";                 / %x31-39 DIGIT         ; 10-99\r\n", e += ";                 / \"1\" 2DIGIT            ; 100-199\r\n", e += ";                 / \"2\" %x30-34 DIGIT     ; 200-249\r\n", e += ";                 / \"25\" %x30-35          ; 250-255\r\n", e += ";statement = 1*( reserved / unreserved / \" \" )\r\n", e += ";scheme        = ALPHA *( ALPHA / DIGIT / \"+\" / \"-\" / \".\" )\r\n", e += ";authority     = [ userinfo \"@\" ] host [ \":\" port ]\r\n", e += ";userinfo      = *( unreserved / pct-encoded / sub-delims / \":\" )\r\n", e += ";query         = *( pchar / \"/\" / \"?\" )\r\n", e += ";fragment      = *( pchar / \"/\" / \"?\" )\r\n", e += ";IPvFuture     = \"v\" 1*HEXDIG \".\" 1*( unreserved / sub-delims / \":\" )\r\n", e += ";reg-name      = *( unreserved / pct-encoded / sub-delims )\r\n", e += ";pct-encoded   = \"%\" HEXDIG HEXDIG\r\n", e += ";pchar         = unreserved / pct-encoded / sub-delims / \":\" / \"@\"\r\n", e += ";path-empty    = 0pchar; deprecated - empty literal string, \"\", is more efficient \r\n", e += ";unreserved    = ALPHA / DIGIT / \"-\" / \".\" / \"_\" / \"~\"\r\n", e += ";reserved      = gen-delims / sub-delims\r\n", e += ";gen-delims    = \":\" / \"/\" / \"?\" / \"#\" / \"[\" / \"]\" / \"@\"\r\n", e += ";sub-delims    = \"!\" / \"$\" / \"&\" / \"'\" / \"(\" / \")\"\r\n", e += ";              / \"*\" / \"+\" / \",\" / \";\" / \"=\"\r\n", e += ";HEXDIG         =  DIGIT / \"A\" / \"B\" / \"C\" / \"D\" / \"E\" / \"F\"\r\n", e += "\r\n", e += "; ------------------------------------------------------------------------------\r\n", e += "; RFC 3339\r\n", e += "\r\n", e += "date-fullyear   = 4DIGIT\r\n", e += "date-month      = 2DIGIT  ; 01-12\r\n", e += "date-mday       = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on\r\n", e += "                          ; month/year\r\n", e += "time-hour       = 2DIGIT  ; 00-23\r\n", e += "time-minute     = 2DIGIT  ; 00-59\r\n", e += "time-second     = 2DIGIT  ; 00-58, 00-59, 00-60 based on leap second\r\n", e += "                          ; rules\r\n", e += "time-secfrac    = \".\" 1*DIGIT\r\n", e += "time-numoffset  = (\"+\" / \"-\") time-hour \":\" time-minute\r\n", e += "time-offset     = \"Z\" / time-numoffset\r\n", e += "\r\n", e += "partial-time    = time-hour \":\" time-minute \":\" time-second\r\n", e += "                  [time-secfrac]\r\n", e += "full-date       = date-fullyear \"-\" date-month \"-\" date-mday\r\n", e += "full-time       = partial-time time-offset\r\n", e += "\r\n", e += "date-time       = full-date \"T\" full-time\r\n", e += "\r\n", e += "; ------------------------------------------------------------------------------\r\n", e += "; RFC 5234\r\n", e += "\r\n", e += "ALPHA          =  %x41-5A / %x61-7A   ; A-Z / a-z\r\n", e += "LF             =  %x0A\r\n", e += "                  ; linefeed\r\n", e += "DIGIT          =  %x30-39\r\n", e += "                  ; 0-9\r\n", e += "HEXDIG         = %d48-57 / %d65-70 / %d97-102\r\n", e += "\r\n", e;
	};
}
//#endregion
//#region lib/utils.ts
var i = (e) => {
	if (e.length !== 42) return "invalid-checksum";
	let t = e.slice(2);
	return t === t.toLowerCase() || t === t.toUpperCase() ? "unchecksummed" : o(e) ? "valid-checksum" : "invalid-checksum";
}, a = (e) => {
	let r = `${e}`.toLowerCase().replace("0x", ""), i = n(t(r)), a = "0x";
	for (let e = 0; e < r.length; e++) parseInt(i[e], 16) >= 8 ? a += r[e].toUpperCase() : a += r[e];
	return a;
}, o = (e) => e.length === 42 ? e === a(e) : !1, s = (e) => {
	let t = parseInt(e);
	if (isNaN(t) || t === Infinity) throw Error("Invalid number.");
	return t;
}, c = /^(?<date>[0-9]{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]))[Tt]([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]|60)(\.[0-9]+)?(([Zz])|([+-]([01][0-9]|2[0-3]):[0-5][0-9]))$/, l = (e) => {
	let t = c.exec(e);
	if (!t) return !1;
	let n = new Date(t.groups.date).toISOString().slice(0, 10);
	return t.groups.date === n;
}, u = e.utils, d = e.ids, f = {
	signInWithEtherium: function(e, t, n, r) {
		switch (e.state) {
			case d.ACTIVE:
				if (typeof r != "object" || !r) throw Error("data must be an object");
				break;
			case d.NOMATCH: r.errors.push(`invalid message: max line number was ${r.lineno}`);
		}
	},
	lineno: function(e, t, n, r) {
		e.state === d.MATCH && (r.lineno += 1);
	},
	exTitle: function(e, t, n, r) {
		e.state === d.NOMATCH && --r.lineno;
	},
	nbTitle: function(e, t, n, r) {
		e.state === d.NOMATCH && --r.lineno;
	},
	riTitle: function(e, t, n, r) {
		e.state === d.NOMATCH && --r.lineno;
	},
	reTitle: function(e, t, n, r) {
		e.state === d.MATCH ? r.resources = [] : e.state === d.NOMATCH && --r.lineno;
	},
	oscheme: function(e, t, n, r) {
		e.state === d.MATCH && (r.scheme = u.charsToString(t, n, e.phraseLength - 3));
	},
	domain: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.domain = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
				r.errors.push(`line ${r.lineno}: domain cannot be empty`);
				break;
			case d.NOMATCH: r.errors.push(`line ${r.lineno}: invalid domain`);
		}
	},
	address: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.address = u.charsToString(t, n, e.phraseLength);
				let a = i(r.address);
				a === "invalid-checksum" ? r.errors.push(`line ${r.lineno}: invalid EIP-55 address checksum - ${r.address}`) : a === "unchecksummed" && r.warnings.push(`line ${r.lineno}: address is not EIP-55 checksummed - ${r.address}`);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid address`);
				break;
		}
	},
	statement: function(e, t, n, r) {
		e.state === d.MATCH && (r.statement = u.charsToString(t, n, e.phraseLength));
	},
	emptyStatement: function(e, t, n, r) {
		e.state === d.MATCH && (r.statement = "");
	},
	version: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.version = u.charsToString(t, n, e.phraseLength);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid version`);
				break;
		}
	},
	nonce: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.nonce = u.charsToString(t, n, e.phraseLength);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid nonce`);
				break;
		}
	},
	issuedAt: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.issuedAt = u.charsToString(t, n, e.phraseLength), l(r.issuedAt) || r.errors.push(`line ${r.lineno}: invalid issued-at date time semantics`);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid issued-at date time syntax`);
				break;
		}
	},
	expirationTime: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.expirationTime = u.charsToString(t, n, e.phraseLength), l(r.expirationTime) || r.errors.push(`line ${r.lineno}: invalid expiration-time date time semantics`);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid expiration-time date time syntax`);
				break;
		}
	},
	notBefore: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.notBefore = u.charsToString(t, n, e.phraseLength), l(r.notBefore) || r.errors.push(`line ${r.lineno}: invalid not-before date time semantics`);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid not-before date time syntax`);
				break;
		}
	},
	requestId: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.requestId = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
				r.requestId = "";
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid requestID`);
				break;
		}
	},
	chainId: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.chainId = s(u.charsToString(t, n, e.phraseLength));
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid chain-id`);
				break;
		}
	},
	uriR: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriR = u.charsToString(t, n, e.phraseLength);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid resource URI`);
				break;
		}
	},
	resource: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.resources.push(r.uriR), delete r.uriR;
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid resource`);
				break;
		}
	},
	scheme: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.scheme = u.charsToString(t, n, e.phraseLength);
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI scheme`);
				break;
		}
	},
	userinfo: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.userinfo = u.charsToString(t, n, e.phraseLength - 1);
				break;
		}
	},
	host: function(e, t, n, r) {
		switch (e.state) {
			case d.ACTIVE:
				r.iplit = !1;
				break;
			case d.MATCH:
				r.iplit ? r.uriElements.host = u.charsToString(t, n + 1, e.phraseLength - 2) : r.uriElements.host = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
				r.uriElements.host = "";
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI host`);
				break;
		}
	},
	ipLiteral: function(e, t, n, r) {
		e.state === d.MATCH && (r.iplit = !0);
	},
	port: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.port = s(u.charsToString(t, n, e.phraseLength));
				break;
			case d.EMPTY:
				r.uriElements.port = "";
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI port`);
				break;
		}
	},
	pathAbempty: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.path = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
				r.uriElements.path = "";
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI path-abempty`);
				break;
		}
	},
	pathAbsolute: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.path = u.charsToString(t, n, e.phraseLength);
				break;
		}
	},
	pathRootless: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.path = u.charsToString(t, n, e.phraseLength);
				break;
		}
	},
	pathEmpty: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI - path-empty must be empty`);
				break;
			case d.EMPTY:
				r.uriElements.path = "";
				break;
		}
	},
	query: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.query = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
				r.uriElements.query = "";
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI query`);
				break;
		}
	},
	fragment: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uriElements.fragment = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
				r.uriElements.fragment = "";
				break;
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI fragment`);
				break;
		}
	},
	uri: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.uri = u.charsToString(t, n, e.phraseLength);
				break;
			case d.EMPTY:
			case d.NOMATCH:
				r.errors.push(`line ${r.lineno}: invalid URI`);
				break;
		}
	},
	ipv4: function(e, t, n, r) {
		e.state === d.MATCH && (r.ipv4 = !0);
	},
	h16: function(e, t, n, r) {
		e.state === d.MATCH && (r.h16count += 1);
	},
	nodcolon: function(e, t, n, r) {
		switch (e.state) {
			case d.ACTIVE:
				r.h16count = 0, r.ipv4 = !1;
				break;
			case d.MATCH:
				r.ipv4 ? r.h16count === 6 ? e.state = d.MATCH : (e.state = d.NOMATCH, e.phraseLength = 0) : r.h16count === 8 ? e.state = d.MATCH : (e.state = d.NOMATCH, e.phraseLength = 0);
				break;
		}
	},
	dcolon: function(e, t, n, r) {
		switch (e.state) {
			case d.ACTIVE:
				r.h16count = 0, r.ipv4 = !1;
				break;
			case d.MATCH:
				r.ipv4 ? r.h16count < 6 ? e.state = d.MATCH : (e.state = d.NOMATCH, e.phraseLength = 0) : r.h16count < 8 ? e.state = d.MATCH : (e.state = d.NOMATCH, e.phraseLength = 0);
				break;
		}
	},
	decOctet: function(e, t, n, r) {
		switch (e.state) {
			case d.ACTIVE:
				r.octet = 0;
				break;
			case d.MATCH:
				r.octet > 255 ? (e.state = d.NOMATCH, e.phraseLength = 0) : e.state = d.MATCH;
				break;
		}
	},
	decDigit: function(e, t, n, r) {
		switch (e.state) {
			case d.MATCH:
				r.octet = 10 * r.octet + t[n] - 48;
				break;
		}
	}
}, p = new r(), m = class e extends Error {
	errors;
	constructor(t) {
		super(t.join("\n")), this.name = "SiweParseError", this.errors = t, Object.setPrototypeOf(this, e.prototype);
	}
}, h = class {
	scheme;
	domain;
	address;
	statement;
	uri;
	version;
	chainId;
	nonce;
	issuedAt;
	expirationTime;
	notBefore;
	requestId;
	resources;
	uriElements;
	warnings;
	constructor(t) {
		let n = new e.parser();
		n.callbacks = Object.create(null), n.callbacks["sign-in-with-ethereum"] = f.signInWithEtherium, n.callbacks.oscheme = f.oscheme, n.callbacks.domain = f.domain, n.callbacks.LF = f.lineno, n.callbacks["ex-title"] = f.exTitle, n.callbacks["nb-title"] = f.nbTitle, n.callbacks["ri-title"] = f.riTitle, n.callbacks["re-title"] = f.reTitle, n.callbacks.address = f.address, n.callbacks.statement = f.statement, n.callbacks["empty-statement"] = f.emptyStatement, n.callbacks.version = f.version, n.callbacks["chain-id"] = f.chainId, n.callbacks.nonce = f.nonce, n.callbacks["issued-at"] = f.issuedAt, n.callbacks["expiration-time"] = f.expirationTime, n.callbacks["not-before"] = f.notBefore, n.callbacks["request-id"] = f.requestId, n.callbacks.uri = f.uri, n.callbacks["uri-r"] = f.uriR, n.callbacks.resource = f.resource, n.callbacks.scheme = f.scheme, n.callbacks["userinfo-at"] = f.userinfo, n.callbacks.host = f.host, n.callbacks["IP-literal"] = f.ipLiteral, n.callbacks.port = f.port, n.callbacks["path-abempty"] = f.pathAbempty, n.callbacks["path-absolute"] = f.pathAbsolute, n.callbacks["path-rootless"] = f.pathRootless, n.callbacks["path-empty"] = f.pathEmpty, n.callbacks.query = f.query, n.callbacks.fragment = f.fragment, n.callbacks.IPv4address = f.ipv4, n.callbacks.nodcolon = f.nodcolon, n.callbacks.dcolon = f.dcolon, n.callbacks.h16 = f.h16, n.callbacks.h16c = f.h16, n.callbacks.h16n = f.h16, n.callbacks.h16cn = f.h16, n.callbacks["dec-octet"] = f.decOctet, n.callbacks["dec-digit"] = f.decDigit;
		let r = {
			errors: [],
			warnings: [],
			lineno: 1,
			scheme: void 0,
			domain: void 0,
			address: void 0,
			statement: void 0,
			uri: void 0,
			version: void 0,
			chainId: void 0,
			nonce: void 0,
			issuedAt: void 0,
			expirationTime: void 0,
			notBefore: void 0,
			requestId: void 0,
			resources: void 0,
			uriElements: {
				scheme: void 0,
				userinfo: void 0,
				host: void 0,
				port: void 0,
				path: void 0,
				query: void 0,
				fragment: void 0
			}
		}, i = n.parse(p, 0, t, r), a = [...r.errors];
		if (i.success || a.push(`Invalid message: ${JSON.stringify(i)}`), a.length > 0) throw new m(a);
		this.warnings = [...r.warnings], this.scheme = r.scheme, this.domain = r.domain, this.address = r.address, this.statement = r.statement, this.uri = r.uri, this.version = r.version, this.chainId = r.chainId, this.nonce = r.nonce, this.issuedAt = r.issuedAt, this.expirationTime = r.expirationTime, this.notBefore = r.notBefore, this.requestId = r.requestId, this.resources = r.resources, this.uriElements = r.uriElements;
	}
}, g = (t) => {
	let n = new e.parser();
	return n.callbacks = Object.create(null), n.callbacks["IP-literal"] = f.ipLiteral, n.callbacks.IPv4address = f.ipv4, n.callbacks.nodcolon = f.nodcolon, n.callbacks.dcolon = f.dcolon, n.callbacks.h16 = f.h16, n.callbacks.h16c = f.h16, n.callbacks.h16n = f.h16, n.callbacks.h16cn = f.h16, n.callbacks["dec-octet"] = f.decOctet, n.callbacks["dec-digit"] = f.decDigit, n.parse(p, "uri-r", t, { errors: [] }).success;
};
//#endregion
export { h as ParsedMessage, m as SiweParseError, i as classifyAddressCase, o as isEIP55Address, g as isUri, l as isValidISO8601Date, s as parseIntegerNumber, a as toChecksumAddress };
