module.exports = {
    module: {
      rules: [
        {
          test: /\.js$|jsx/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader"
          }
        },
        {
          test: /\.css$/,
          use: [ 'style-loader', 'css-loader']
        },
        {
          test: /\.(woff|woff2|ttf|svg|eot)$/,
          use: [
              {
                  loader: 'file-loader',
                  options: {}
              }
          ]
        }
      ]
    }
  };