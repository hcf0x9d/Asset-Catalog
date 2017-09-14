/**
 * Grab the querystring and return an object
 *
 * @returns {{}}
 */
var parseQueryString = function() {

    var str = window.location.search;
    var objURL = {};

    str.replace(
        new RegExp( "([^?=&]+)(=([^&]*))?", "g" ),
        function( $0, $1, $2, $3 ){
            objURL[ $1 ] = $3;
        }
    );
    return objURL;
};


/**
 * Add New Item Class Constructor
 *
 * Instead of doing a post to open a window for adding a new item to a category
 * we will pop a lightbox for the user to add their input, then post that
 * information to the DB and refresh the same category view (reload)
 *
 * @constructor
 */
function AddNewItem() {

    var _this = this;

    _this.button = document.getElementById( 'newItemButton' );

    _this.handleEvents = function () {

        _this.button.addEventListener( 'click', function () {

            _this.popModal('open');

        } );

    };

    _this.popModal = function ( action ) {

        if ( action === 'open' ) {
            // Open the modal window


        } else {
            // Destroy the modal
        }


    };


    _this.handleEvents();
    // TODO: Pop a modal window
    //
}


function deleteItem(delObj) {

    swal({
        title: 'Do you want to remove this item?',
        text: 'This will remove the item from your catalog. You cannot undo this.',
        input: 'email',
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'No, cancel!',
        confirmButtonClass: 'btn btn-success',
        cancelButtonClass: 'btn btn-danger',
        buttonsStyling: false
    },
    function () {
        $.ajax( {
            type: "post",
            url: "/deleteItem",
            data: delObj,
            success: function( data ){
            }
        } )
        .done(function(data) {
            swal("Item removed!", "This item was removed from the catalog!", "success");
            // Remove the item on the client side
        })
        .error(function(data) {
            swal("Oops", "We couldn't connect to the server!", "error");
        });
    });

}