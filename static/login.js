const form = document.getElementById('login-form');
const errorEl = document.getElementById('error');
const resultEl = document.getElementById('result');

form.addEventListener('submit', async (e) => {
	e.preventDefault();
	errorEl.textContent = '';
	resultEl.textContent = '';

	const body = new URLSearchParams();
	body.append('username', form.username.value);
	body.append('password', form.password.value);
	body.append('grant_type', 'password');

	try {
		const res = await fetch('/api/token', {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: body
		});

		const data = await res.json();

		if (!res.ok) {
			if (res.status == 400 && data.detail) {
				errorEl.textContent = data.detail.error_description || data.error
				return
			} else if (res.status == 422 && data.detail) {
				const field = data.detail[0].loc[data.detail[0].loc.length - 1]
				const msg = data.detail[0].msg
				errorEl.textContent = `${field}: ${msg}`
				return
			} else if (res.status == 500 && data.detail) {
				errorEl.textContent = data.detail
				return
			}
			throw new Error("Something went wrong")
		}

		resultEl.textContent = 'Login successful!';
		form.reset();

		console.log('Access token:', data.access_token);
	} catch (err) {
		errorEl.textContent = 'Network or server error';
	}
});
