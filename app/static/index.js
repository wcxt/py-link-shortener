const form = document.getElementById("shorten-form");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");

form.addEventListener("submit", async (e) => {
	e.preventDefault()

	errorEl.textContent = ""
	resultEl.textContent = ""

	const url = form.url.value.trim()

	try {
		const res = await fetch("/api/short", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ url })
		})

		const data = await res.json()

		if (!res.ok) {
			if (res.status == 422 && data.detail) {
				errorEl.textContent = data.detail[0].msg
				return
			} else if (res.status == 500 && data.detail) {
				errorEl.textContent = data.detail
				return
			}
			throw new Error("Something went wrong")
		}
		const short_url = `${window.location.origin}/${data.short_code}`
		resultEl.innerHTML = `Short URL: <a href="${short_url}" target="_blank">${short_url}</a>`
		form.reset()
	} catch (error) {
		errorEl.textContent = error.message
	}
})
