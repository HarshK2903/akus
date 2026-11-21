/** Match the server's application/pdf input contract and SHA-256 check. */
export async function preparePdf(file: File) {
  if (!file.size || file.size > 2097152 || file.type !== "application/pdf")
    throw new Error("Choose a nonempty PDF of 2 MiB or less.");
  const bytes = new Uint8Array(await file.arrayBuffer());
  const digest = Array.from(
    new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    (b) => b.toString(16).padStart(2, "0"),
  ).join("");
  let raw = "";
  for (let i = 0; i < bytes.length; i += 8192)
    raw += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return {
    digest,
    attachment: { media_type: "application/pdf", base64_data: btoa(raw) },
  };
}
