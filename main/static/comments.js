pushPage = function(page) {
	window.history.pushState(page, "title", "/space/"+space+"/document/"+document_hash+"?page="+page);
}

pageLoaded = function() {
	loadComments(curpage);
}


function loadComments(page) {
	$.getJSON("/space/"+space+"/document/"+document_hash+"/page/" + page + "/comments", function(data) {
		$("#comments").empty();
		$.each(data, function(i, comment) {
			var c = $("<div class='comment'></div>");
			var edit_link = $("<a class=\"edit\" href=\"#\">edit</a>").click(function() {
				$("#post-comment #id_nickname").val(comment['nickname_plain']);
				$("#post-comment #id_comment").val(comment['comment_plain']);
				$("#post-comment #comment-cancel").css("display", "inline");
				$("#post-comment #comment-id").val(comment['id']);
				$("#post-comment-header").html("Edit Comment");
				return false;
			});
			var delete_link = $("<a class=\"delete\" href=\"#\">delete</a>").click(function() {
				$.ajax({
					url: '/space/'+space+'/document/'+document_hash+'/deletecomment/'+comment['id'],
					type: 'get'
				}).done(function(data) {
					loadComments(curpage);
				});
				return false;
			});
			var head = $("<div class='comment-head'></div>");
			var links = $("<div class='comment-links'></div>");
			$(links).append(delete_link).append(edit_link);
			$(head).append("<span class='comment-nickname'>" + comment['nickname'] + "</span>");
			$(head).append(links);
			$(c).append(head);
			$(c).append("<div class='comment-comment'>" + comment['comment'] + "</div>");

			c.appendTo("#comments");
		});
		MathJax.Hub.Queue(["Typeset", MathJax.Hub, $("#comments")[0]]);
		SyntaxHighlighter.highlight();
	});
}

function rename() {
	var newname = window.prompt("Please enter a new name for the document:", document_name);
	if(newname == null || newname.length == 0) { return; }
	$.ajax({
		url: '/space/'+space+'/document/'+document_hash+'/rename',
		type: 'post',
		data: {name: newname}
	}).done(function(data) {
		if(data.status == 0) {
			if('name_escaped' in data) {
				document_name = data.name_escaped;
				document.title = document_name;
				$('.current_document_name').html(document_name);
			}
		}
		else {
			var error = 'message' in data ? data.message : 'An unknown error occurred.';
			alert('The document could not be renamed: '+ error);
		}
	});
}

$(function() {

	$("#post-comment").submit(function(event) {
		$.ajax({
			url: '/space/'+space+'/document/'+document_hash+'/page/' + curpage + '/comment',
			type: "post",
			data: $(this).serialize()
		}).done(function(data) {
			if(data.status == 0) {
				$("#post-comment #id_comment").val("");
				$("#post-comment #comment-id").val("");
				$("#post-comment #comment-cancel").css("display", "none");
				$("#post-comment-header").html("New Comment");
				loadComments(curpage);
				if (data.safenick) {
					setNickname(data.safenick);
				}
			}
			else {
				alert('The comment could not be submitted: '+data.message);
			}
		});
		event.preventDefault();
	});
	$("#post-comment #comment-cancel").click(function() {
		$("#post-comment #id_comment").val("");
		$("#post-comment #comment-id").val("");
		$(this).css("display", "none");
		return false;
	});
	
	window.onpopstate = function(e){
		if(e.state) {
			displayPage(e.state);
		}
		else {
			displayPage(startpage);
		}
	};

	splitCookies();
	if('nickname' in cookies && cookies.nickname.length > 0) {
		setNickname(cookies.nickname);
	}

	loadDocument(space, document_hash, document_name, document_page);
});
