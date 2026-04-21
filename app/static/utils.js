export function setAccessToken(token) {
	localStorage.setItem("access_token", token)
}

export function logout() {
	localStorage.removeItem("access_token")
	window.location.replace("/")
}

export function getAccessToken() {
	return localStorage.getItem("access_token")
}

export function fetchWithBearer(url, options) {
	token = getAccessToken()
	if (!token) {
		throw new Error("Access token is required")
	}

	return fetch(url, {
		...options,
		headers: {
			...options.headers,
			Authorization: `Bearer ${token}`
		}
	})
}
