// CSRF proof is not an identity token. Opaque authentication lives only in HttpOnly cookies.
const key = "akus.demo.csrf";
export const sessionCsrf = {
  get: () => sessionStorage.getItem(key) ?? "",
  set: (value: string) => sessionStorage.setItem(key, value),
  clear: () => sessionStorage.removeItem(key),
};
