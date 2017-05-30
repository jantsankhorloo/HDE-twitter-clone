jQuery(function($) {
    // Grab whatever we need to paginate
    var pageParts = $(".paginate");

    // How many parts do we have?
    var numPages = pageParts.length;
    // How many parts do we want per page?
    var perPage = 5;

    // When the document loads we're on page 1
    // So to start with... hide everything else
    pageParts.slice(perPage).hide();
    // Apply simplePagination to our placeholder
    $("#page-nav").pagination({
        items: numPages,
        itemsOnPage: perPage,
        cssStyle: "dark-theme",
        // We implement the actual pagination
        //   in this next function. It runs on
        //   the event that a user changes page
        onPageClick: function(pageNum) {
            // Which page parts do we show?
            var start = perPage * (pageNum - 1);
            var end = start + perPage;

            // First hide all page parts
            // Then show those just for our page
            pageParts.hide()
                     .slice(start, end).show();
        }
    });
});