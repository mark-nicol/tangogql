import React, {Component} from "react";
import { findDOMNode } from "react-dom";
import { connect } from 'react-redux'
import { sprintf } from 'sprintf-js'
import Plotly from "Plotly"


class AttributeTrend extends Component {

    _cache = {}
    
    constructor () {
        super();
        this.state = {data: []}
    }
    
    componentDidMount() {
        const node = findDOMNode(this.refs.trend);
        const data = [
            {
                x: [],
                y: [],
                type: 'scatter',
                mode: "lines",
                name: "hello",
                showlegend: true,
                yaxis: "y1",
                legendgroup: "0"
            }
        ];
        const layout = {
            // title: this.props.label || this.props.name,
            // autosize: true,
            width: node.offsetWidth,
            height: 300,
            showlegend: true,
            xaxis: {
                type: "date",
                zerolinecolor: '#aaa'
                // range: [
                //     (new Date()).getTime() - 3600 * 1000,
                //     (new Date()).getTime()
                // ]
            },
            yaxis: {
                zerolinecolor: '#aaa'
            },
            yaxis2: {
                side: "right",
                overlaying: 'y',
                showgrid: false,
                zeroline: false
            },
            legend: {
                // yanchor:"middle",
                // traceorder: "grouped",
                font: {
                    size: 14
                },
                bgcolor: 'rgba(255,255,255,0.75)',
                y: 1,
                x: 0,
            },            
            // paper_bgcolor: 'rgba(0,0,0,0)',
            margin: {
                l: 50,
                r: 20,
                b: 40,
                t: 10,
                // pad: 4
            }        
        }
        Plotly.newPlot(node, data, layout, {displayModeBar: false});                    
    }
    
    shouldComponentUpdate() {
        return false;
    }

    componentWillReceiveProps (props) {

        
        const node = findDOMNode(this.refs.trend);
        console.log("trrend node", node);
        let data = {x: [], y: [],
                    name: this.props.listeners.map(l => this.props.configs[l]? this.props.configs[l].label || this.props.configs[l].name : l)}
        let updatedLines = []
        this.props.listeners.forEach((model, i) => {
            const history = this.props.history[model] || {x: [], y: []};
            // if (history == this._cache[model])
            //     return
            this._cache[model] = history;
            data.x.push(history.x)
            data.y.push(history.y)
            updatedLines.push(i)
        })

        console.log("history", data);
        let layout = {
            xaxis: {
                type: "date",
                range: [
                    (new Date()).getTime() - this.props.historySize*1000,
                    (new Date()).getTime() + 1000
                ]
            },
            yaxis: {
                title: props.configs[props.listeners[0]]? props.configs[props.listeners[0]].unit : ""
            },
        }
        console.log("layout", layout)
        while (this.props.listeners.length > node.data.length)
            Plotly.addTraces(node, {x: [], y: [], yaxis: "y2", legendgroup: "1",
                                    type: "scatter", mode: "lines"})
                    
        Plotly.relayout(node, {width: node.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.clientWidth - 10, height: node.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.clientHeight - 30, ...layout})
        Plotly.restyle(node, data, updatedLines);
    }
    
    render () {
        return <div className="container" ref="container">
            <div className="trend" ref="trend"/>
            </div>
    }
            
}

AttributeTrend.defaultProps = {
    historySize: 5*60
}



function select (state) {
    return {
        attributes: state.data.attributes,
        values: state.data.attribute_values,
        configs: state.data.attribute_configs,
        history: state.data.attribute_value_history
    }
}


export default connect(select)(AttributeTrend);
