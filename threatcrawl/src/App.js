import * as React from 'react';
import { Component } from 'react';
import { BrowserRouter, HashRouter, Route, Switch } from 'react-router-dom';
import { StylesProvider, ThemeProvider } from '@material-ui/styles';
import { createMuiTheme } from "@material-ui/core";
import './App.css';
import StartMain from './start_screen/StartMain';
import TabScreen from './start_screen/TabScreen';
import ConfigurationSelection from './start_screen/ConfigurationSelection';
import TrainingMain from './training_screen/TrainingMain';
import DoubleCheck from './training_screen/DoubleCheck';

class App extends Component {

    render() {
        const theme = createMuiTheme({
            typography: {
                allVariants: {
                    color: 'white'
                }
            },
            palette: {
                type: "dark",
                primary: {
                    main: '#c5c0f2'
                }
            }
        });

        return (
            <div className="App">
                <StylesProvider injectFirst>
                    <ThemeProvider theme={theme}>
                        {(!process.env.NODE_ENV || process.env.NODE_ENV === 'development') ?
                            <BrowserRouter>
                                <Switch>
                                    <Route exact path="/start" component={StartMain} />
                                    <Route exact path="/config" component={TabScreen} />
                                    <Route exact path="/configselect" component={ConfigurationSelection} />
                                    <Route exact path="/training" component={TrainingMain} />
                                    <Route exact path="/doublecheck" component={DoubleCheck} />
                                </Switch>
                            </BrowserRouter>
                            :
                            <HashRouter>
                                <Switch>
                                    <Route exact path="/start" component={StartMain} />
                                    <Route exact path="/config" component={TabScreen} />
                                    <Route exact path="/configselect" component={ConfigurationSelection} />
                                    <Route exact path="/training" component={TrainingMain} />
                                    <Route exact path="/doublecheck" component={DoubleCheck} />
                                </Switch>
                            </HashRouter>
                        }
                    </ThemeProvider>
                </StylesProvider>
            </div>
        );
    }
}

export default App;
