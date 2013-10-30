'use strict';
module.exports = function (grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        sass: {
            dist: {
                options: {
                    compass: true,
                    lineNumbers: true
                    // style: 'compressed'
                },
                files: {
                    'genweb/theme/stylesheets/genwebupc.css': 'genweb/theme/scss/genwebupc.scss'
                }
            }
        },
        watch: {
            scripts: {
                files: ['genweb/theme/scss/*.scss',],
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
        }
    });

    // grunt.loadTasks('tasks');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-bless');
    grunt.registerTask('default', ['watch']);
};
