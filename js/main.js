import React from "react";
import { render } from "react-dom";
import { createStore, applyMiddleware, combineReducers } from 'redux';
import { normalize, Schema, arrayOf } from 'normalizr';
import { Provider } from 'react-redux'
import createLogger from 'redux-logger';
import thunkMiddleware from 'redux-thunk'
import Lokka from "lokka";
import Transport from "lokka-transport-http"
import HTML5Backend from 'react-dnd-html5-backend';
import { DragDropContext } from 'react-dnd';

import data from "./store.js";
import AttributeListenerList from "./attribute";
import Tree from "./tree"
import {fetchDomain, fetchFamily, fetchMember} from "./store";
import {receiveChange, receiveConfig, setDashboardLayout,
        ADD_ATTRIBUTE_LISTENER, REMOVE_ATTRIBUTE_LISTENER} from "./actions";
import TangoDashboard from "./dashboard";


// redux store

const logger = createLogger();

const createStoreWithMiddleware = applyMiddleware(
    thunkMiddleware // lets us dispatch() functions
    , logger // logs all actions to console for debugging
)(createStore)

function lastAction(state = null, action) {
    return action;
}

const rootReducer = combineReducers({
    data,
    lastAction  // used by the websocket hack below
});

let store = createStoreWithMiddleware(rootReducer);


// GUI

let mainContainer = document.getElementById("container");

class _App extends React.Component {

    render() {
        return (
                <section id="inner" className="main hbox space-between">            
                <nav id="tree">
                <Tree pattern="*" store={this.props.store}/>
                </nav>
                <article id="main">
                <TangoDashboard width={500}/>
                </article>
                </section>
        );
    }
    
}

const App = DragDropContext(HTML5Backend)(_App);1

render(
        <Provider store={store}>
        <App/>
        </Provider>,
    mainContainer
)


/* hacking a websocket in "on top" of the redux store... 
This might be better done through middleware?*/

var ws = new WebSocket("ws://" + window.location.host + "/socket", "json");


ws.addEventListener("message", msg => {
    console.log(msg.data)
    var data = JSON.parse(msg.data);
    data.events.forEach(e => store.dispatch(e));
});


ws.addEventListener("open", () => {
    console.log("Websocket open!")
});


ws.addEventListener("error", (e) => {
    console.log("Websocket error!", e)
});


function wsListener () {
    let {session, lastAction} = store.getState();
    if (!lastAction)
        return
    switch (lastAction.type) {
    case ADD_ATTRIBUTE_LISTENER:
        let model = `${lastAction.data.device}/${lastAction.data.attribute}`;
        ws.send(JSON.stringify({"type": "SUBSCRIBE",
                                "models": [model]}));
        break;
    case REMOVE_ATTRIBUTE_LISTENER:
        ws.send(JSON.stringify({"type": "UNSUBSCRIBE",
                                "models": [lastAction.data.model]}));
        break;
    }
}


store.subscribe(wsListener);
