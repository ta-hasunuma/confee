/**
 * IPホワイトリスト定義
 * WAF IPSet と CloudFront Function の両方で使用する
 */
export const ALLOWED_IPS: string[] = [
  "66.159.192.8",
  "66.159.192.9",
  "66.159.200.79",
  "114.141.123.64",
  "114.141.123.65",
  "137.83.216.7",
  "137.83.216.125",
  "208.127.111.180",
];

/** WAF IPSet 用の CIDR 表記 */
export const ALLOWED_IP_CIDRS: string[] = ALLOWED_IPS.map(
  (ip) => `${ip}/32`
);
