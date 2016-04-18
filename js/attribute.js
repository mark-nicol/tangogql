import React, {Component} from "react";
import { connect } from 'react-redux'
import { sprintf } from 'sprintf-js'

import {removeAttributeListener} from './actions';


class AttributeListener extends Component {

    onClick () {
        this.props.dispatch(removeAttributeListener(this.props.model));
    }
    
    render () {
        return (
                <div className="attribute" onClick={this.onClick.bind(this)}>
                <span className="label">{this.props.label}</span>
                <span className={"value " + this.props.quality}>
                <span>
                {this.props.format?
                 sprintf(this.props.format, this.props.value) :
                 this.props.value}
                </span>
                </span>
                <span className="unit">{this.props.unit}</span>
                </div>);
    }
}


class AttributeList extends Component {
    render () {
        let attrs = this.props.listeners.map((item, i) => {
            let model = `${item.device}/${item.attribute}`;
            let attr = this.props.attributes[model] || {};
            let value = this.props.values[model] || {};
            let config = this.props.configs[model] || {};
            return <AttributeListener key={i}  model={model} name={attr.name}
                      value={value? value.value : null}
                      quality={value? value.quality : "UNKNOWN"}            
                      label={config? config.label || attr.name : attr.name}
                      unit={config? config.unit || "" : ""}
                      format={config? config.format : null}            
                      dispatch={this.props.dispatch}/>
        });

        return <div className="attribute-list">{attrs}</div>;
    }
}


function select (state) {
    return {
        attributes: state.data.attributes,
        values: state.data.attribute_values,
        configs: state.data.attribute_configs
    }
}


export default connect(select)(AttributeList);
