// Generated on 2015-01-23 using generator-angular 0.10.0
'use strict';

// # Globbing
// for performance reasons we're only matching one level down:
// 'test/spec/{,*/}*.js'
// use this if you want to recursively match all subfolders:
// 'test/spec/**/*.js'

module.exports = function (grunt) {

  // Load grunt tasks automatically
  require('load-grunt-tasks')(grunt);

  // Time how long tasks take. Can help when optimizing build times
  require('time-grunt')(grunt);

  // Configurable paths for the application
  var appConfig = {
    dist: 'genweb/theme/dist',
    egg: 'genweb/theme'
  };

  var config_file = 'config.json';
  var resource_config = grunt.file.readJSON(config_file);

  // Define the configuration for all the tasks
  grunt.initConfig({

    // Project settings
    yeoman: appConfig,

    sass: {
        dist: {
            options: {
                compass: true,
                // style: 'compressed'
            },
            files: {
                'genweb/theme/stylesheets/genwebupc.css': 'genweb/theme/scss/genwebupc.scss'
            }
        }
    },
    // Watches files for changes and runs tasks based on the changed files
    watch: {
      gw: {
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

    // Empties folders to start fresh
    clean: {
      dist: {
        files: [{
          dot: true,
          src: [
            '.tmp',
            '<%= yeoman.dist %>/{,*/}*',
            '!<%= yeoman.dist %>/.git{,*/}*'
          ]
        }]
      },
      server: '.tmp'
    },

    // Renames files for browser caching purposes
    filerev: {
      dist: {
        src: [
          '<%= yeoman.dist %>/scripts/{,*/}*.js',
          '<%= yeoman.dist %>/styles/{,*/}*.css',
          '<%= yeoman.dist %>/images/{,*/}*.{png,jpg,jpeg,gif,webp,svg}',
          '<%= yeoman.dist %>/styles/fonts/*'
        ]
      },
      build: {
        src: [
          '<%= yeoman.dist %>/{,*/}*.css',
        ]
      }
    },

    // The following *-min tasks will produce minified files in the dist folder
    // By default, your `index.html`'s <!-- Usemin block --> will take care of
    // minification. These next options are pre-configured if you do not wish
    // to use the Usemin blocks.
    cssmin: {
      dist: {
        files: {
          '<%= yeoman.dist %>/vendor.css': resource_config.css.development
        }
      }
    },

    htmlmin: {
      dist: {
        options: {
          collapseWhitespace: true,
          conservativeCollapse: true,
          collapseBooleanAttributes: true,
          removeCommentsFromCDATA: true,
          removeOptionalTags: true
        },
        files: [{
          expand: true,
          cwd: '<%= yeoman.dist %>',
          src: ['*.html', 'views/{,*/}*.html'],
          dest: '<%= yeoman.dist %>'
        }]
      }
    },

  });

  // Not used because it's done in Python side but kept for reference
  grunt.registerTask('replacepaths', function () {
    resource_config.css_true_path = [];
    resource_config.js_true_path = [];
    for (var key in resource_config.replace_map) {
      if (resource_config.replace_map.hasOwnProperty(key)) {
        var value = resource_config.replace_map[key];
        if (resource_config.hasOwnProperty('css')) {
          resource_config.css.development.forEach(function (obj) {
            if (obj.indexOf(key) !== -1) {
              // grunt.log.write('Replacing: ' + key + ' \nwith value:' + value + ' in CSS resources.\n');
              resource_config.css_true_path.push(obj.replace(key, value));
            }
          });
        }
        if (resource_config.hasOwnProperty('js')) {
          resource_config.js.development.forEach(function (obj) {
            if (obj.indexOf(key) !== -1) {
              // grunt.log.write('Replacing: ' + key + ' \nwith value:' + value + ' in JS resources.\n');
              resource_config.js_true_path.push(obj.replace(key, value));
            }
          });
        }
       }
    }
    var vendor_css_file = appConfig.dist + '/vendor.css';
    var updated_cssmin_config = {cssmin: {dist: {files: {}}}};
    updated_cssmin_config.cssmin.dist.files[vendor_css_file] = resource_config.css_true_path;
    grunt.config.merge(updated_cssmin_config);
    // grunt.config.merge({cssmin: {dist: {files: {vendor_css_file: resource_config.css_true_path}}}});
    grunt.log.write(JSON.stringify(grunt.config.getRaw('cssmin')));
      // grunt.log.write(JSON.stringify(resource_config.css_true_path));
      // grunt.log.write(JSON.stringify(resource_config.js_true_path));

  });

  grunt.registerTask('debug', function () {
      grunt.log.write(resource_config.css_true_path);
    });

  grunt.registerTask('updateconfig', function () {
    if (!grunt.file.exists(config_file)) {
        grunt.log.error('file ' + config_file + ' not found');
        return true; //return false to abort the execution
    }

    resource_config.revision_info = grunt.filerev.summary; //edit the value of json object, you can also use projec.key if you know what you are updating

    grunt.file.write(config_file, JSON.stringify(resource_config, null, 2)); //serialize it back to file

    });

  grunt.registerTask('default', [
    'watch',
  ]);

  grunt.registerTask('gwbuild', [
    // 'replacepaths', // Not used, intended to be replaced on Python side
    'clean:dist',
    'cssmin:dist',
    'filerev:build',
    'updateconfig'
  ]);

};
