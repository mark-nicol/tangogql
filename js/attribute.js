import React, {Component} from "react";
import { connect } from 'react-redux'
import { sprintf } from 'sprintf-js'

import {removeAttributeListener} from './actions';


class AttributeListener extends Component {

    onClick () {
        this.props.dispatch(removeAttributeListener(this.props.model));
    }
    
    render () {
        return (<div className="attribute" onClick={this.onClick.bind(this)}>
                {this.props.label}:
                <span className={this.props.quality}>
                {this.props.format?
                 sprintf(this.props.format, this.props.value):
                 this.props.value}
                </span>
                {this.props.unit}
                </div>);
    }
}


class AttributeListenerList extends Component {
    render () {
        let attrs = Object.keys(this.props.listeners).map((model, i) => {
            let attr = this.props.attributes[model]
            let value = this.props.values[model]
            let config = this.props.configs[model]            
            return <AttributeListener key={i}  model={model} name={attr.name}
                      value={value? value.value : null}
                      quality={value? value.quality : "UNKNOWN"}            
                      label={config? config.label || attr.name : attr.name}
                      unit={config? config.unit || "" : ""}
                      format={config? config.format : null}            
                      dispatch={this.props.dispatch}/>
        });

        return <div>{attrs}</div>;
    }
}


function select (state) {
    return {
        listeners: state.data.listeners,
        attributes: state.data.attributes,
        values: state.data.attribute_values,
        configs: state.data.attribute_configs
    }
}

export default connect(select)(AttributeListenerList);
