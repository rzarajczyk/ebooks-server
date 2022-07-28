$(() => {
	M.AutoInit();

	const queryString = window.location.search
	const params = new URLSearchParams(queryString)
	if (params.get('status') == 'ok') {
		$('#upload-successful').show()
	}
	$('#close-info').click(() => {
		$('#upload-successful').hide()
	})
})
