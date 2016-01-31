module.exports = {
    entry: "./js/main.js",
    output: {
        path: __dirname + "/static/js",
        filename: "bundle.js"
    },
    module: {
        loaders: [
            { test: /\.jsx?$/, exclude: /node-modules/, loader: "babel-loader" }
        ]
    },
    resolve: {
        extensions: [ "", ".js", ".jsx" ]
    }
};
