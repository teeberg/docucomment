var cookies = {};

function splitCookies() {
	// Declare variables.
	var subElements = document.cookie.split("&");
	var subElemPairs = new Array();
	var subNameValues = new Array();

	// Obtain sub-element names and values.
	for (i = 0; i < subElements.length; i++)
	{
	    subElemPairs[i] = subElements[i].split("=");
	}

	// Place sub-element name-value pairs in an associative array.
	for (i = 0; i < subElemPairs.length; i++)
	{
	    cookies[subElemPairs[i][0]] = subElemPairs[i][1];
	}
	return cookies;
}

function changeNickname() {
	var nickname = 'nickname' in cookies ? cookies.nickname : '';
	var newname = window.prompt("Please enter a new nickname:", nickname);
	if(newname == null || newname.length == 0) { return; }

	$.ajax({
		url: '/setnickname',
		type: 'post',
		data: {name: newname}
	}).done(function(data) {
		data = JSON.parse(data);
		setNickname(data.safenick);
	});
}

function setNickname(nickname) {
	cookies.nickname = nickname;
	$('.current_nickname').html(nickname);
	$('#info_commenting_as').css('visibility', 'visible');
	$('#id_nickname').parent().css('display', 'none');
	$('#id_nickname').val(nickname);
}
