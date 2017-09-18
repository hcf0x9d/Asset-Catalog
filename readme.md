# Asset Catalog Web Application

I went ahead and made this project far more difficult than I needed, as such, it has some functionality holes in it.  Not that the functionality doesn't work, it's just lacking in areas like having multiple JSON endpoints.

## Installation
Review the dependencies below, make sure everything is ready before installing

### Dependencies
- You need a Google Plus account to use this application, they are free. Go get one.
- [Vagrant](https://www.vagrantup.com/)
- [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
- Google+ Client Secrets(client_secrets.json)


### How to Install
1. Install Vagrant & VirtualBox
2. Clone this repo into a parent directory
2. Add the Udacity Vagrantfile to the parent directory
3. `cd catalog` from the parent directory
3. Launch the Vagrant VM (`vagrant up`)
4. Log into Vagrant VM (`vagrant ssh`)
7. Initialize the sqlite database `python model.py`
9. Run application using `python view_controller.py`
10. Access the application locally using http://localhost:5000

## JSON Endpoints
The following are open:

Category Items JSON: `/api/<string:category_slug>/items`
    - Displays items for a specific category

Item JSON: `/api/<string:category_slug>/<string:item_slug>`
    - Displays information for a single item