const form = document.getElementById('login-form');
const errorEl = document.getElementsById('error');
const resultEl = document.getElementById('result');

form.addEventListener('submit', async (e) => {
	e.preventDefault();
	errorEl.textContent = '';
	resultEl.textContent = '';

	const body = new URLSearchParams();
	body.append('username', form.username.value);
	body.append('password', form.password.value);
	body.append('grant_type', 'password');
	body.append('client_type', 'web');

	try {
		const res = await fetch('/api/token', {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: body,
		});

		const data = await res.json();

		if (!res.ok) {
			if (res.status == 400 && data.error) {
				errorEl.textContent = data.error_description || data.error
				return
			} else if (res.status == 500 && data.detail) {
				errorEl.textContent = data.detail
				return
			}
			throw new Error("Something went wrong")
		}

		resultEl.textContent = 'Login successful!';
		form.reset();
	} catch (err) {
		errorEl.textContent = 'Network or server error';
	}
});
