const path = require('path');

module.exports = {
    // Should be STATIC_URL + path/to/build
    publicPath: '/static/src/vue/dist/',

    // Output to a directory in STATICFILES_DIRS
    outputDir: path.resolve(__dirname, '../yaksh/static/src/vue/dist/'),

    // Django will hash file names, not webpack
    filenameHashing: false,

    // See: https://vuejs.org/v2/guide/installation.html#Runtime-Compiler-vs-Runtime-only
    runtimeCompiler: true,

    devServer: {
        writeToDisk: true, // Write files to disk in dev mode, so Django can serve the assets
    },

    pluginOptions: {
      quasar: {
        importStrategy: 'kebab',
        rtlSupport: false
      }
    },

    transpileDependencies: [
      'quasar'
    ]
};
