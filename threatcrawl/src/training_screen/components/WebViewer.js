import * as React from 'react';
import { Component } from 'react';
import Snackbar from '@material-ui/core/Snackbar';
import MuiAlert from '@material-ui/lab/Alert';

import '../../styles/training.css';

class WebViewer extends Component {

    constructor(props) {
        super(props)

        this.state = {
            showAlert: false
        }
    }

    componentDidMount() {
        // Add onclick listener for highlighting
        this.attachOnClickListener();
    }

    /**
     * Handle clicking on the webviewer
     */
    handleClick = event => {
        event.preventDefault();

        // Make sure a label is selected
        if (! this.props.label && this.props.showAlert) {
            this.setState({
                showAlert: true
            });
            return;
        }

        // Call the handle click event from the props on the clicked element
        try {
            if (typeof this.props.handleClick === 'function') {
                this.props.handleClick(event.target);
            }
        } catch (error) {
            console.log('An error occured during the execution of the user-provided handleClick method', error);
        }
    }

    /**
     * Handle closing the popup
     */
     handleClose = (event, reason) => {
        // If the user clicked away don't close the popup
        if (reason === 'clickaway') {
            return;
        }

        // Otherwise do close the popup
        this.setState({
            showAlert: false
        });
    };

    /**
     * Attach an onClick listener to the viewer
     */
    attachOnClickListener() {
        document.getElementById('viewer').onload = () => {
            const iframe_document = document.getElementById("viewer").contentDocument;

            iframe_document.body.addEventListener('click', this.handleClick);

            try {
                this.props.on_load();
            } catch (error) { /** Do nothing, we don't care about any user-code errors here */ }
        };
    }

    render() {
        return (
            <div className="WebViewer">
                {/* Render the viewer using sandbox to disable all external communication */}
                <iframe id="viewer" title="viewer" src={this.props.page_url} sandbox="true"></iframe>
                <>
                    {/* The popup to render if needed */}
                    <Snackbar open={this.state.showAlert}
                        autoHideDuration={6000}
                        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
                        onClose={this.handleClose}>
                        <MuiAlert elevation={6} variant="filled" severity="info" onClose={this.handleClose}>
                            Please select a label first!
                        </MuiAlert>
                    </Snackbar>
                </>
            </div>
        );
    }
}

export default WebViewer;