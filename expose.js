module.exports = function(grunt) {

  'use strict';

  var _ = grunt.util._;

  function isValidMultiTaskTarget(target) {
    return !/^_|^options$/.test(target);
  }

  function formatTask(value, key, list) {
    list[key].targets = Object.keys(grunt.config.getRaw(key) || {}).filter(isValidMultiTaskTarget);
    list[key].multi = !!list[key].multi;
  }

  grunt.registerTask(
    'expose', "Expose available tasks as JSON object.", function () {
      var tasks = grunt.task._tasks;
      _.each(tasks, formatTask);
      grunt.log.write("EXPOSE_BEGIN" + JSON.stringify(tasks) + "EXPOSE_END");
    }
  );
};