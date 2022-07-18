window.DATA = []

function render(data) {
	var result = '<ul>'
	for (var i = 0; i < data.length; i++) {
		var book = data[i]
		result += '<li>'
		result += '<a href="' + book.mobi + '" class="cover"><img src="' + book.cover + '" /></a>'
		result += '<a href="' + book.mobi + '" class="authors">' + book.authors + '</a>'
		result += '<a href="' + book.mobi + '" class="title">' + book.title + '</a>'
		result += '<div class="clear"></div>'
		result += '</li>'
	}
	$('#content').html(result)
}

$.get('/books', function (data) {
	console.log(data)
	window.DATA = data
	render(data)
})

$('#search').keyup(function () {
	var text = $('#search').val()
	var filtered = window.DATA.filter(function (it) {
		return it.title.indexOf(text) >= 0 || it.authors.indexOf(text) >= 0
	})
	render(filtered)
})
