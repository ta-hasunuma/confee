import { ALLOWED_IPS, ALLOWED_IP_CIDRS } from "../lib/config/allowed-ips";

describe("allowed-ips", () => {
  test("ALLOWED_IPSに8つのIPアドレスが定義されている", () => {
    expect(ALLOWED_IPS).toHaveLength(8);
  });

  test("ALLOWED_IPSに要件で指定された全IPアドレスが含まれる", () => {
    const expectedIps = [
      "66.159.192.8",
      "66.159.192.9",
      "66.159.200.79",
      "114.141.123.64",
      "114.141.123.65",
      "137.83.216.7",
      "137.83.216.125",
      "208.127.111.180",
    ];
    expect(ALLOWED_IPS).toEqual(expectedIps);
  });

  test("ALLOWED_IP_CIDRSが/32 CIDR表記である", () => {
    expect(ALLOWED_IP_CIDRS).toHaveLength(8);
    for (const cidr of ALLOWED_IP_CIDRS) {
      expect(cidr).toMatch(/^\d+\.\d+\.\d+\.\d+\/32$/);
    }
  });

  test("ALLOWED_IP_CIDRSがALLOWED_IPSに対応する", () => {
    const expectedCidrs = ALLOWED_IPS.map((ip) => `${ip}/32`);
    expect(ALLOWED_IP_CIDRS).toEqual(expectedCidrs);
  });
});
