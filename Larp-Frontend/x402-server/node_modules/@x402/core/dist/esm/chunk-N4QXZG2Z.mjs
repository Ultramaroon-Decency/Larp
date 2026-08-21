// src/schemas/index.ts
import { z } from "zod";
import { z as z2 } from "zod";
var NonEmptyString = z.string().min(1);
var Any = z.record(z.unknown());
var OptionalAny = z.record(z.unknown()).optional().nullable();
var NetworkSchemaV1 = NonEmptyString;
var NetworkSchemaV2 = z.string().min(3).refine((val) => val.includes(":"), {
  message: "Network must be in CAIP-2 format (e.g., 'eip155:84532')"
});
var NetworkSchema = z.union([NetworkSchemaV1, NetworkSchemaV2]);
var PRINTABLE_ASCII_REGEX = /^[\x20-\x7e]+$/;
var ResourceInfoSchema = z.object({
  url: NonEmptyString,
  description: z.string().nullish().transform((v) => v ?? void 0),
  mimeType: z.string().nullish().transform((v) => v ?? void 0),
  serviceName: z.string().min(1).max(32).regex(PRINTABLE_ASCII_REGEX).nullish().transform((v) => v ?? void 0),
  tags: z.array(z.string().min(1).max(32).regex(PRINTABLE_ASCII_REGEX)).max(5).nullish().transform((v) => v ?? void 0),
  iconUrl: z.string().max(2048).nullish().transform((v) => v ?? void 0)
});
var PaymentRequirementsV1Schema = z.object({
  scheme: NonEmptyString,
  network: NetworkSchemaV1,
  maxAmountRequired: NonEmptyString,
  resource: NonEmptyString,
  // URL string in V1
  description: z.string(),
  mimeType: z.string().optional(),
  outputSchema: Any.optional().nullable(),
  payTo: NonEmptyString,
  maxTimeoutSeconds: z.number().positive(),
  asset: NonEmptyString,
  extra: OptionalAny
});
var PaymentRequiredV1Schema = z.object({
  x402Version: z.literal(1),
  error: z.string().optional(),
  accepts: z.array(PaymentRequirementsV1Schema).min(1)
});
var PaymentPayloadV1Schema = z.object({
  x402Version: z.literal(1),
  scheme: NonEmptyString,
  network: NetworkSchemaV1,
  payload: Any
});
var PaymentRequirementsV2Schema = z.object({
  scheme: NonEmptyString,
  network: NetworkSchemaV2,
  amount: NonEmptyString,
  asset: NonEmptyString,
  payTo: NonEmptyString,
  maxTimeoutSeconds: z.number().positive(),
  extra: OptionalAny
});
var PaymentRequiredV2Schema = z.object({
  x402Version: z.literal(2),
  error: z.string().nullish().transform((v) => v ?? void 0),
  resource: ResourceInfoSchema,
  accepts: z.array(PaymentRequirementsV2Schema).min(1),
  extensions: OptionalAny
});
var PaymentPayloadV2Schema = z.object({
  x402Version: z.literal(2),
  resource: ResourceInfoSchema.nullish().transform((v) => v ?? void 0),
  accepted: PaymentRequirementsV2Schema,
  payload: Any,
  extensions: OptionalAny
});
var PaymentRequirementsSchema = z.union([
  PaymentRequirementsV1Schema,
  PaymentRequirementsV2Schema
]);
var PaymentRequiredSchema = z.discriminatedUnion("x402Version", [
  PaymentRequiredV1Schema,
  PaymentRequiredV2Schema
]);
var PaymentPayloadSchema = z.discriminatedUnion("x402Version", [
  PaymentPayloadV1Schema,
  PaymentPayloadV2Schema
]);
function parsePaymentRequired(value) {
  return PaymentRequiredSchema.safeParse(value);
}
function validatePaymentRequired(value) {
  return PaymentRequiredSchema.parse(value);
}
function isPaymentRequired(value) {
  return PaymentRequiredSchema.safeParse(value).success;
}
function parsePaymentRequirements(value) {
  return PaymentRequirementsSchema.safeParse(value);
}
function validatePaymentRequirements(value) {
  return PaymentRequirementsSchema.parse(value);
}
function isPaymentRequirements(value) {
  return PaymentRequirementsSchema.safeParse(value).success;
}
function parsePaymentPayload(value) {
  return PaymentPayloadSchema.safeParse(value);
}
function validatePaymentPayload(value) {
  return PaymentPayloadSchema.parse(value);
}
function isPaymentPayload(value) {
  return PaymentPayloadSchema.safeParse(value).success;
}
function isPaymentRequiredV1(value) {
  return PaymentRequiredV1Schema.safeParse(value).success;
}
function isPaymentRequiredV2(value) {
  return PaymentRequiredV2Schema.safeParse(value).success;
}
function isPaymentRequirementsV1(value) {
  return PaymentRequirementsV1Schema.safeParse(value).success;
}
function isPaymentRequirementsV2(value) {
  return PaymentRequirementsV2Schema.safeParse(value).success;
}
function isPaymentPayloadV1(value) {
  return PaymentPayloadV1Schema.safeParse(value).success;
}
function isPaymentPayloadV2(value) {
  return PaymentPayloadV2Schema.safeParse(value).success;
}

export {
  NonEmptyString,
  Any,
  OptionalAny,
  NetworkSchemaV1,
  NetworkSchemaV2,
  NetworkSchema,
  ResourceInfoSchema,
  PaymentRequirementsV1Schema,
  PaymentRequiredV1Schema,
  PaymentPayloadV1Schema,
  PaymentRequirementsV2Schema,
  PaymentRequiredV2Schema,
  PaymentPayloadV2Schema,
  PaymentRequirementsSchema,
  PaymentRequiredSchema,
  PaymentPayloadSchema,
  parsePaymentRequired,
  validatePaymentRequired,
  isPaymentRequired,
  parsePaymentRequirements,
  validatePaymentRequirements,
  isPaymentRequirements,
  parsePaymentPayload,
  validatePaymentPayload,
  isPaymentPayload,
  isPaymentRequiredV1,
  isPaymentRequiredV2,
  isPaymentRequirementsV1,
  isPaymentRequirementsV2,
  isPaymentPayloadV1,
  isPaymentPayloadV2,
  z2 as z
};
//# sourceMappingURL=chunk-N4QXZG2Z.mjs.map