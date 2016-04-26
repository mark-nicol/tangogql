import React, {Component} from "react";
import { findDOMNode } from "react-dom";
import { connect } from 'react-redux'
import { sprintf } from 'sprintf-js'
import Plotly from "Plotly"

import {removeAttributeListener} from './actions';


class SpectrumAttribute extends Component {

    _cache = null

    getCardWidth () {
        // a tediuos (and fragile) hack to get the width of the card
        const node = findDOMNode(this.refs.plot);
        return node.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.clientWidth
    }
    
    componentDidMount() {
        const node = findDOMNode(this.refs.plot);
        const data = [
            {
                // x: ['2013-10-04 22:23:00', '2013-11-04 22:23:00', '2013-12-04 22:23:00'],
                y: [],
                type: 'scatter'
            }
        ];
        const layout = {
            title: this.props.label || this.props.name,
            //autosize: true,
            width: this.getCardWidth(),
            height: 150,
            paper_bgcolor: 'rgba(0,0,0,0)',
            margin: {
                l: 50,
                r: 0,
                b: 25,
                t: 35,
                pad: 4
            },
            yaxis: {
                nticks: 3,
                tickformat: ".1e",
                type: "log",
                tickmode: "linear"
            }
        }
        Plotly.newPlot(node, data, layout, {displayModeBar: false});
    }
    
    shouldComponentUpdate() {
        return false;
    }

    componentWillReceiveProps (props) {
        if (props.value === this._cache)  // also check label, etc!
            return
        this._cache = props.value;
        const node = findDOMNode(this.refs.plot);
        const min = Math.min(...props.value), max = Math.max(...props.value);
        Plotly.relayout(node, {width: this.getCardWidth()-20,
                               yaxis: {nticks: 3, type: "log", tickmode: "array", tickformat: ".1e",
                                       tickvals: [min, max], ticktext: [0, 1]}})
        Plotly.restyle(node, {y: [props.value]}, 0);
    }
    
    render () {
        return <tr className="attribute" onClick={this.props.onRemove} style={{height: "150px"}}>
               <td colSpan={3} className="plot" ref="plot"/>
               </tr>
    }
    
}


class ScalarAttribute extends Component {

    shouldComponentUpdate (props) {
        return props.value !== this.props.value || props.name != this.props.name || props.label != this.props.label
            || props.unit != this.props.unit || props.quality != this.props.quality;
    }
    
    render() {
        return (
                <tr onClick={this.props.onRemove} className="attribute">
                <td className="label">{this.props.label}</td>
                <td className={"value " + this.props.quality}>
                    <span>
                      {this.props.format?
                       sprintf(this.props.format, this.props.value) :
                       this.props.value}
                    </span>
                </td>
                <td className="unit">{this.props.unit}</td>
             </tr>
        );
    }
}


class AttributeListener extends Component {

    render () {
        if (this.props.data_format == "SPECTRUM")
            return <SpectrumAttribute {...this.props}/>
        return <ScalarAttribute {...this.props}/>
    }
}


class AttributeList extends Component {

    onRemoveAttribute (attr) {
        
    }

    getAttributeComponent (model, i) {

        let attr = this.props.attributes[model],
            value = this.props.values[model],
            config = this.props.configs[model];
        
        return <AttributeListener key={i} model={model}
                       name={attr? attr.name : "?"}
                       value={value? value.value : null}
                       quality={value? value.quality : "UNKNOWN"}            
                       label={config? config.label || (attr? attr.name : "?") :
                              attr? attr.name : "?"}
                       unit={config? config.unit || "" : ""}
                       format={config? config.format : null}            
                       data_format={config? config.data_format : null}
                       dispatch={this.props.dispatch}
                       onRemove={()=>this.props.onRemoveAttribute(model)}/>
    }
    
    render () {
        let attrs = this.props.listeners.map(this.getAttributeComponent.bind(this));
        //return <div className="attribute-list">{attrs}</div>;
        return <table className="attribute-list"><tbody>{attrs}</tbody></table>;
    }
}



function select (state) {
    return {
        attributes: state.data.attributes,
        values: state.data.attribute_values,
        configs: state.data.attribute_configs,
        history: state.data.attribute_value_history
    }
}


export default connect(select)(AttributeList);
