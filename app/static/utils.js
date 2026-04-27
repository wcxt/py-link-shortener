async function logout() {
	const res = await fetch("/api/token", {
		method: "DELETE"
	});

	if (!res.ok) {
		data = await res.json();
		if (res.status == 500 && data.detail) {
			alert(data.detail);
			return;
		}
		alert("Something went wrong");
		return;
	}

	window.location.href = "/";
}