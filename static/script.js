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

    _this.openButton = document.getElementById( 'newItemButton' );

    /**
     * All Add New Item events can be handled here
     */
    _this.handleEvents = function () {

        // Be able to open the lightbox
        _this.openButton.addEventListener( 'click', function () {

            _this.popModal( 'open' );

        } );

        // // Close the lightbox
        // _this.closeButton.addEventListener( 'click', function () {
        //
        //     _this.popModal( 'destroy' )
        //
        // } );

    };

    /**
     * Lightbox handling events
     *
     * @param action - String :: what do you want to do?
     */
    _this.popModal = function ( action ) {

        if ( action === 'open' ) {

            swal( {
                title: 'Add a new item',
                type: 'question',
                html:
                    '<input id="js-item-name" class="swal2-input" placeholder="Category Name">' +
                    '<textarea id="js-item-description" class="swal2-input" placeholder="Description"></textarea>',
                showCancelButton: true,
                confirmButtonText: 'Submit',
                showLoaderOnConfirm: true,
                preConfirm: function ( text ) {
                    return new Promise ( function ( resolve, reject ) {
                        resolve( {
                            "name": $('#js-item-name').val(),
                            "description": $('#js-item-description').val(),
                            "category_id": $('#js-category').val(),
                            "slug": $('#js-item-name').val().replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()
                        } );
                    } )
                },
                allowOutsideClick: false
            } ).then( function ( result ) {
                console.log(result)
                $.ajax( {
                    url: '/addItem',
                    type: 'POST',
                    data: result,
                    dataType: 'json'
                } )
                .done(function( ){

                    window.location.reload();
                })
                .fail(function(){
                   swal('Oops...', 'Something went wrong with ajax!', 'error');
                });
            } );

        }

    };

    // Kick off the handler
    _this.handleEvents();

}

function editItem () {
    swal( {
        title: 'Update Item',
        type: 'question',
        html:
            '<input id="js-item-name" class="swal2-input" placeholder="Item Name" value="' + $('.name').text().trim() + '">' +
            '<textarea id="js-item-description" class="swal2-input" placeholder="Description" rows="5" style="height:auto;">' + $('.description').text().trim() + '</textarea>',
        showCancelButton: true,
        confirmButtonText: 'Submit',
        showLoaderOnConfirm: true,
        preConfirm: function ( text ) {
            return new Promise ( function ( resolve, reject ) {
                resolve( {
                    "name": $('#js-item-name').val(),
                    "id": $('#article').attr('data-id'),
                    "description": $('#js-item-description').val(),
                    "slug": $('#js-item-name').val().replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()
                } );
            } )
        },
        allowOutsideClick: false
    } ).then( function ( result ) {

        $.ajax( {
            url: '/updateItem',
            type: 'POST',
            data: result,
            dataType: 'json'
        } )
        .done(function( ){

            window.location.reload();
        })
        .fail(function(){
           swal('Oops...', 'Something went wrong with ajax!', 'error');
        });
    } );
}


/**
 * Add New Item Class Constructor
 *
 * Instead of doing a post to open a window for adding a new item to a category
 * we will pop a lightbox for the user to add their input, then post that
 * information to the DB and refresh the same category view (reload)
 *
 * @constructor
 */
function AddNewCategory( inline ) {

    var _this = this;

    _this.startButton = document.querySelector( '.js-new-category' );
    _this.inputWrap = document.getElementById( 'newCategoryWrap' );
    _this.saveButton = document.querySelector( '.js-add-category' );
    _this.closeButton = document.querySelector( '.js-revert-add' );

    /**
     * All Add New Item events can be handled here
     */
    _this.handleEvents = function () {


        // Be able to open the lightbox
        _this.startButton.addEventListener( 'click', function () {

            var action = 'open';

            if ( inline !== true ) {

                action = 'swal'

            }

            _this.popWrap( action );

        });

        if ( inline === true ) {

            _this.closeButton.addEventListener('click', function () {

                _this.popWrap('destroy');

            });

            _this.saveButton.addEventListener('click', function () {

                _this.submitCategory();

            });
        }

    };

    /**
     * Lightbox handling events
     *
     * @param action - String :: what do you want to do?
     */
    _this.popWrap = function ( action ) {

        if ( action === 'open' ) {
            // Open the modal window
            $( _this.inputWrap ).slideDown( 250 );

        } else if ( action === 'destroy' ) {

            // Destroy the modal
            $( _this.inputWrap ).slideUp( 250 );

        } else if ( action === 'swal' ) {

            swal( {
                title: 'Name your category',
                type: 'question',
                html:
                    '<input id="swal-name" class="swal2-input" placeholder="Category Name">' +
                    '<select id="swal-icon" class="swal2-input" name="">' +
                        '<option value="fa-folder-o">Select an Icon</option>' +
                        '<option value="fa-camera-retro">Photgraphy</option>' +
                        '<option value="fa-music">Musical Instruments</option>' +
                        '<option value="fa-tree">Outdoors</option>' +
                        '<option value="fa-desktop">Electronics</option>' +
                        '<option value="fa-automobile">Transportation</option>' +
                        '<option value="fa-bicycle">Exercise</option>' +
                        '<option value="fa-home">Home</option>' +
                        '<option value="fa-play-circle-o">Music</option>' +
                        '<option value="fa-barcode">Other</option>' +
                    '</select>',
                showCancelButton: true,
                confirmButtonText: 'Submit',
                showLoaderOnConfirm: true,
                preConfirm: function ( text ) {
                    return new Promise ( function ( resolve, reject ) {
                        resolve( {
                            "name": $('#swal-name').val(),
                            "icon": $('#swal-icon').val(),
                            "slug": $('#swal-name').val().replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()
                        } );
                    } )
                },
                allowOutsideClick: false
            } ).then( function ( result ) {
                $.ajax( {
                    url: '/addCategory',
                    type: 'POST',
                    data: result
                } )
                .done(function( ){

                    window.location.reload();
                })
                .fail(function(){
                   swal('Oops...', 'Something went wrong with ajax!', 'error');
                });
            } );

        }

    };


    _this.submitCategory = function ( ) {
        var obj = {};

        obj.name = $( '#newCategoryNameInput' ).val();
        obj.slug = obj.name.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()

        $.ajax({
            url: '/addCategory',
            type: 'POST',
            data: obj
        })
        .done( function(){

            window.location.reload();

        })
        .fail( function () {

           swal( 'Oops...', 'Something went wrong with ajax!', 'error' );

        });

    };

    // Kick off the handler
    _this.handleEvents();

}


function deleteCategory( slug ) {

    swal( {
        title: 'Remove this category?',
        text: 'Any items in this category will be moved to "Uncategorized"',
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Remove category',
        cancelButtonText: 'Stop',
        showLoaderOnConfirm: true,
        preConfirm: function() {
            return new Promise(function(resolve) {
                delObj = {"slug": slug};

                $.ajax({
                    url: '/deleteCategory',
                    type: 'POST',
                    data: delObj,
                    dataType: 'json'
                })
                .done(function(response){

                    $('.categoryList-item[data-slug="' + delObj.slug + '"]').slideUp(250);

                    swal('Item removed', 'The item has been removed from your catalog', 'success');

                })
                .fail(function(){
                   swal('Oops...', 'Something went wrong with ajax!', 'error');
                });

                // $.ajax( {
                //     url: '/api/' + slug + '/items',
                //     type: 'POST',
                //     dataType: 'json'
                // } ).done( function ( response ) {
                //
                //     for ( var obj in response.items ) {
                //
                //         console.log( obj );
                //
                //         // if ( obj.hasOwnProperty( obj ) ) count++;
                //
                //     }
                //
                // } ).fail( function () {
                //
                //    swal('Oops...', 'Something went wrong with ajax!', 'error');
                //
                // } );
            });
        },
        allowOutsideClick: false
    });
}


function deleteItem(delObj, goToCategory) {
    delObj = {"id": delObj};
    console.log(delObj)
    swal({
        title: 'Do you want to remove this item?',
        text: 'This will remove the item from your catalog. You cannot undo this.',
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'No, cancel!',
        showLoaderOnConfirm: true,
        preConfirm: function() {
            return new Promise(function(resolve) {
                $.ajax({
                    url: '/deleteItem',
                    type: 'POST',
                    data: delObj,
                    dataType: 'json'
                })
                .done(function(response){
                   swal('Item removed', 'The item has been removed from your catalog', 'success');
                   if (goToCategory) {

                       window.location.href = '/' + goToCategory;

                   } else {

                       hideInView(delObj)

                   }
                })
                .fail(function(){
                   swal('Oops...', 'Something went wrong with ajax!', 'error');
                });
            });
        },
        allowOutsideClick: false
    });

}

function hideInView(obj) {

    $('li[data-id="' + obj.id + '"]').slideUp(250);

}

window.onload = function () {
    var msg  = $( '.flashes li' );

    if ( msg.length > 0 ) {


        swal( {
            text: $(msg).text(),
            type: $(msg).attr('data-type'),
            timer: 1500
        } )
    }
}