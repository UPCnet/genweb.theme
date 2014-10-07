'use strict';
module.exports = function (grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        sass: {
            dist: {
                options: {
                    compass: true,
                    lineNumbers: true,
                    // require: ['sass-css-importer-load-paths',],
                    // style: 'compressed'
                },
                files: {
                    'genweb/theme/stylesheets/genwebupc.css': 'genweb/theme/scss/genwebupc.scss'
                }
            }
        },
        watch: {
            scripts: {
                files: ['genweb/theme/scss/*.scss', 'genweb/theme/bootstrap/scss/compass_twitter_bootstrap/*.scss'],
                tasks: ['sass', 'bless']
            }
        },
        bless: {
            css: {
              options: {},
              files: {
                'genweb/theme/stylesheets/genwebupc-ie.css': 'genweb/theme/stylesheets/genwebupc.css'
              }
            }
        },
        copy: {
          main: {
            files: [
                {
                    expand: true,
                    cwd: '../genweb.alternatheme/genweb/alternatheme/components/fontawesome/css',
                    src:'font-awesome.css',
                    dest:'font-awesome.scss',
                    rename: function(dest, src) {
                        return '../genweb.alternatheme/genweb/alternatheme/components/fontawesome/css/' + dest;
                    }
                },
                {
                    expand: true,
                    cwd: '../genweb.alternatheme/genweb/alternatheme/components/fontawesome/css',
                    src:'font-awesome.css',
                    dest:'font-awesome.less',
                    rename: function(dest, src) {
                        return '../genweb.alternatheme/genweb/alternatheme/components/fontawesome/css/' + dest;
                    }
                },
            ]
          },
        },
    });

    // grunt.loadTasks('tasks');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-bless');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.registerTask('default', ['watch']);
};
