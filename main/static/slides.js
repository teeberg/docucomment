
var hash;
var doc;
var docs = {};
var curpage = 0;
var startpage;
var document_name;
var pushPage = function(page) {};
var pageLoaded = function() {};
var documentLoaded = function() {};

function displayPage(pagenumber) {
	doc.getPage(pagenumber).then(function(page) {
		var scale = 1.5;
		var viewport = page.getViewport(scale);
		var canvas = document.getElementById('slide-canvas');
		var context = canvas.getContext('2d');
		canvas.height = viewport.height;
		canvas.width = viewport.width;
		page.render({canvasContext: context, viewport: viewport});
		curpage = pagenumber;
		$("#slide-page").html("Page " + curpage + " of " + doc.numPages);
		$("#slide-page").attr("href", "/space/" + space + "/document/" + hash + "?page=" + pagenumber);
		$("#link-to-document").val("[[" + document_name + "]]");
		$("#link-to-document-with-text").val("[[" + document_name + "|Some Text]]");
		$("#link-to-page").val("[[" + document_name + "/" + pagenumber + "]]");
		$("#link-to-page-with-text").val("[[" + document_name + "/" + pagenumber + "|Some Text]]");
		pageLoaded();
	});
}

function gotoPage(page) {
	if(page != curpage) {
		pushPage(page);
		displayPage(page);
	}
}

function nextPage() {
	if(curpage < doc.numPages) {
		gotoPage(curpage+1);
	}
}

function previousPage() {
	if(curpage > 1) {
		gotoPage(curpage-1);
	}
}

function loadDocument(space, h, name, page) {
	if (hash == h) {
		displayPage(startpage);
	} else {
		PDFJS.disableWorker = true;
		var func = function() {
			hash = h;
			document_name = name;
			startpage = Math.max(1,Math.min(doc.numPages,page))
			displayPage(startpage);
		};
		if (docs[h]) {
			doc = docs[h];
			func();
			documentLoaded();
		} else {
			PDFJS.getDocument("/space/" + space + "/document/" + h + "/file").then(function(p) {
				doc = p;
				docs[h] = doc;
				func();
				documentLoaded();
			});
		}
	}
}

$(function() {
	$(document).keydown(function(e) {
		var target = e.target.tagName.toLowerCase();
		if(!e.shiftKey && !e.altKey && target != 'input' && target != 'textarea') {
			if(e.keyCode == 37) {
				// left arrow
				var newpage = curpage;
				if(e.ctrlKey) { newpage -= 5; }
				else          { newpage--; }

				gotoPage(Math.max(1, newpage));
				return false;
			}
			else if(e.keyCode == 39) {
				// right arrow
				var newpage = curpage;
				if(e.ctrlKey) { newpage += 5; }
				else          { newpage++; }

				gotoPage(Math.min(newpage, doc.numPages));
				return false;
			}
			else if(!e.ctrlKey) {
				if(e.keyCode == 82) {
					// R
					loadComments(curpage);
					return false;
				}
				else if(e.keyCode == 35) {
					// End key
					gotoPage(doc.numPages);
					return false;
				}
				else if(e.keyCode == 36) {
					// Home key
					gotoPage(1);
					return false;
				}
			}
		}
	});
	$(".first").click(function() {
		gotoPage(0);
		return false;
	});
	$(".prev").click(function() {
		previousPage();
		return false;
	});
	$(".next").click(function() {
		nextPage();
		return false;
	});
	$(".last").click(function() {
		gotoPage(doc.numPages);
		return false;
	});
});

