import React, {Component} from "react";
import { findDOMNode } from "react-dom";
import { connect } from 'react-redux'
import { sprintf } from 'sprintf-js'

import {removeAttributeListener} from './actions';


class ScalarAttributeListener extends Component {

    onClick () {
        this.props.onRemove();
    }
    
    render () {
        return (<div className="attribute" onClick={this.onClick.bind(this)}>
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


class SpectrumAttributeListener extends Component {

    onClick () {
        this.props.dispatch(removeAttributeListener(this.props.model));
    }

    componentDidMount () {
        const node = findDOMNode(this.refs.container);
        
    }
    
    render () {
        return (<div ref="container" className="attribute"
                     onClick={this.onClick.bind(this)}>
                </div>);
    }
}


class AttributeList extends Component {

    onRemoveAttribute (attr) {
        
    }
    
    render () {
        let attrs = this.props.listeners.map((model, i) => {
            let attr = this.props.attributes[model],
                value = this.props.values[model],
                config = this.props.configs[model];
            return <ScalarAttributeListener key={i} model={model}
                       name={attr? attr.name : "?"}
                       value={value? value.value : null}
                       quality={value? value.quality : "UNKNOWN"}            
                       label={config? config.label || (attr? attr.name : "?") :
                              attr? attr.name : "?"}
                       unit={config? config.unit || "" : ""}
                       format={config? config.format : null}            
            dispatch={this.props.dispatch}
            onRemove={()=>this.props.onRemoveAttribute(model)}/>
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
