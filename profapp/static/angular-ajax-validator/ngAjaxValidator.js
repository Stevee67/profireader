(function (angular) {
    'use strict';
    if (!angular) {
        throw 'No angular found';
    }

    var AppendParameter = function (url, var_val) {
        var hashpart = url.match(/^([^#]*)(#(.*))?$/)
        var ret = hashpart[1] + (hashpart[1].match(/\?/) ? '&' : '?') + var_val + (hashpart[2] ? hashpart[2] : '')
        return ret
    };

    var cloneIfExistsAttributes = function (cloneto, defaultparams, params) {

        $.each(defaultparams, function (ind, val) {
            cloneto[ind] = ((typeof params[ind] === 'undefined') ? val : params[ind]);
        });
        return cloneto;
    };

    var cloneIfExistsCallbacks = function (cloneto, defaultparams, params, $scope) {

        $.each(defaultparams, function (ind, val) {
            cloneto[ind] = ((typeof params[ind] === 'undefined') ? val : $scope[ind]);
        });
        return cloneto;
    };


    // url builders


    var retfirtsytapam = function (p, d) {
        return function (p, d) {
            return p
        }
    };


    angular.module('ajaxFormModule', []).factory('$af', ['$ok', function ($ok) {

        var modelsForValidation = [];

        var ret = {};

        ret.$storeModelForValidation = function (model, scope) {
            modelsForValidation.push({model: model, scope: scope, http: null});
        };

        ret.$getValidationDict = function (model) {
            var found = null;
            $.each(modelsForValidation, function (ind, val) {
                if (val && val['model'].$modelValue === model) {
                    found = modelsForValidation[ind];
                    return false;
                }
            });
            return found;
        };

        ret.$callDirectiveMethod = function (model, method, action) {
            var found = ret.$getValidationDict(model);
            return found ? (action ? found['scope'][method](action) : found['scope'][method]()) : null;
        };

        ret.save = function (model) {
            return ret.$callDirectiveMethod(model, 'save');
        };
        ret.load = function (model) {
            return ret.$callDirectiveMethod(model, 'load');
        };
        ret.validate = function (model) {
            return ret.$callDirectiveMethod(model, 'validate');
        };
        ret.isActionAllowed = function (model, action) {
            return ret.$callDirectiveMethod(model, 'isActionAllowed', action);
        };
        return ret;

    }]).directive('af', ['$af', '$ok', '$timeout', function ($af, $ok, $timeout) {
//TODO: OZ by OZ: interact with model validation features (prestine, dirty, valid)
        return {
            restrict: 'A',
            scope: {
                'model': '=ngModel',
                'afBeforeLoad': '&',
                'afAmidLoad': '&',
                'afAfterLoad': '&',
                'afBeforeValidate': '&',
                'afAmidValidate': '&',
                'afAfterValidate': '&',
                'afBeforeSave': '&',
                'afAmidSave': '&',
                'afAfterSave': '&',
                'afWatch': '&'
            },
            require: ['ngModel'],
            link: function ($scope, el, attrs, afModelCtrl) {

                var $parent = $scope['$parent'];
                var ctrl = afModelCtrl[0];


                var params = {};

                cloneIfExistsAttributes(params, {'af-url': window.location.href}, attrs);
                var trans = '';
                if (attrs['afLoadTranslate']) {
                    trans = '&__translate=' + attrs['afLoadTranslate'];
                }
                else {
                    if (attrs['afLoadTranslate'] === '') {
                        trans = '&__translate=' + $parent.controllerName;
                    }
                }
                cloneIfExistsAttributes(params, {
                    'afUrlLoad': AppendParameter(params['af-url'], 'action=load' + trans),
                    'afUrlValidate': AppendParameter(params['af-url'], 'action=validate'),
                    'afUrlSave': AppendParameter(params['af-url'], 'action=save')
                }, attrs);

//TODO oz by OZ: allow model name dictionary

                cloneIfExistsAttributes(params, {
                    'afDebounce': '500',
                    'afLoadResult': (attrs.ngModel + '_original'),
                    'afValidationResult': attrs.ngModel + '_validation',
                    'afSaveResult': attrs.ngModel + '_saved',
                    'afState': attrs.ngModel + '_state'
                }, attrs);

                params['afDebounce'] = parseInt(params['afDebounce']);
                if (params['afDebounce'] <= 0) params['afDebounce'] = 500;

                var trivialbefore = function () {
                    return function (model, default_function) {
                        return model;
                    }
                };

                var defaultCallbacks = {
                    afBeforeLoad: trivialbefore,
                    afAmidLoad: trivialbefore,
                    afBeforeValidate: trivialbefore,
                    afAmidValidate: trivialbefore,
                    afAmidSave: trivialbefore,
                    afBeforeSave: trivialbefore,
                    afAfterLoad: function () {
                        return function (resp) {
                            setInParent('afLoadResult', cloneObject(resp));
                            return true;
                        }
                    },
                    afAfterValidate: function () {
                        return function (resp) {
                            setInParent('afValidationResult', cloneObject(resp));
                            return true;
                        }
                    },
                    afAfterSave: function () {
                        return function (resp) {
                            setInParent('afSaveResult', cloneObject(resp));
                            return true;
                        };
                    }
                };

                cloneIfExistsCallbacks(params, defaultCallbacks, attrs, $scope);

                function callCallback() {
                    var args = Array.prototype.slice.call(arguments);
                    var callbackkey = args.shift();
                    args.push(defaultCallbacks[callbackkey]());
                    var func = params[callbackkey]();
                    if (func === undefined) {
                        func = defaultCallbacks[callbackkey]();
                    }
                    var ret = func.apply($parent, args);
                    return ret;
                }

                var setInParent = function (ind, val) {
                    $parent[params[ind]] = val;
                };


                var func1 = function (action, statebefore, stateonok, stateonfail, ok, notok) {
                    ok = ok ? ok : function () {
                    };
                    notok = notok ? notok : function () {
                    };
                    //debugger;
                    var validationdict = $af.$getValidationDict($scope['model']);
                    try {
                        var dataToSend = callCallback('afBefore' + action, $scope['model']);
                        var url = params['afUrl' + action];
                        setInParent('afState', statebefore);
                        var promise = $ok(url, dataToSend ? dataToSend : {},
                            function (resp, errorcode, httpresp) {
                                try {
                                    var ret = callCallback('afAmid' + action, resp);
                                    ok(ret);
                                    if (stateonok) setInParent('afState', stateonok);
                                    $timeout(function () {
                                        callCallback('afAfter' + action, ret)
                                    }, 0);
                                }
                                catch (e) {
                                    console.error(e);
                                    if (stateonfail) setInParent('afState', stateonfail);
                                    notok(resp);
                                }
                            },
                            function (resp, errorcode, httpresp) {
                                if (stateonok) setInParent('afState', stateonfail);
                                notok(resp, errorcode);
                            }).finally(function () {
                                validationdict['http'] = null;
                            });
                        if (validationdict) {
                            validationdict['http'] = promise;
                        }
                        return true;
                    }
                    catch (e) {
                        console.error(e);
                        if (stateonok) setInParent('afState', stateonfail);
                        notok(undefined);
                        validationdict['http'] = null;
                    }
                };


                $scope.load = function () {
                    if ($scope.isActionAllowed('load')) {
                        func1('Load', 'loading', 'clean', 'loading_failed',
                            function (resp) {
                                $scope.model = cloneObject(resp);
                            });
                    }
                };

                $scope.validate = function () {
                    if ($scope.isActionAllowed('validate')) {
                        func1('Validate', 'validating', false, 'validating_failed',
                            function (resp) {
                                if ($parent[params['afState']] === 'validating') {
                                    setInParent('afState', !resp['errors'] || Object.keys(resp['errors']).length ? 'invalid' : 'valid');
                                }
                            });
                    }
                    else {
                        debouncedvalidate();
                    }
                };

                $scope.save = function () {
                    if ($scope.isActionAllowed('save')) {
                        func1('Save', 'saving', 'clean', 'saving_failed')
                    }
                };

                $scope.isActionAllowed = function (action) {
                    var http = $af.$getValidationDict($scope['model']);
                    if (http && http['http']) {
                        //console.error('called method `' + action + '` is forbidden for model because http sent');
                        return false;
                    }
                    var allowed_states = {'save': ['init', 'clean', 'saving_failed', 'valid', 'loading_failed']};
                    allowed_states['load'] = allowed_states['save'] + ['dirty', 'validating_failed', 'invalid'];
                    allowed_states['validate'] = allowed_states['load'];

                    if (allowed_states[action].indexOf($parent[params['afState']]) === -1) {
                        //console.error('called method `'+action+'` is forbidden for model because current model is in state: `' + $parent[params['afState']] + '`');
                        return false;
                    }
                    return true;
                };

                $af.$storeModelForValidation(ctrl, $scope);
                setInParent('afState', 'init');

                $scope.load();

                var debouncedvalidate = _.debounce(function () {
                    $scope.validate();
                }, params['afDebounce']);

                var watchfunc = function (oldval, newval) {
                    setInParent('afState', 'dirty');
                    debouncedvalidate();
                };

                $timeout(function () {
                    $parent.$watch(attrs['afWatch'] ? attrs['afWatch'] : attrs['ngModel'], watchfunc, true)
                }, 0, false);
            }
        };


    }]).directive('afValidationAnswer', [function () {

        var watch_functions = {};
        return {
            restrict: "A",
            replace: false,
            //$scope: {
            //    afValidationAnswer: '&'
            //},
            template: function (tElement, tAttrs) {
                var model_fields = tAttrs['afValidationAnswer'].split(':');
                var model_name = model_fields[0];
                var field_name = model_fields[1];
                var erm = '' + model_name + '.errors.' + field_name;
                var ewm = '' + model_name + '.warnings.' + field_name;
                var enm = '' + model_name + '.notices.' + field_name;
                return '<span class="error"   ng-if="' + erm + '"><span class="icon icon-stop"></span> {{ ' + erm + ' }}</span>' +
                    '<span class="warning" ng-if="!' + erm + ' && ' + ewm + '"><span class="icon icon-warning"></span> {{ ' + ewm + ' }}</span>' +
                    '<span class="notice"  ng-if="!' + erm + ' && ! ' + ewm + ' && ' + enm + '"><span class="icon icon-check"></span> {{ ' + enm + ' }}</span>';
            },
            scope: false,
            link: function ($scope, iElement, iAttrs, ngModelCtrl) {

            }
        }
    }]);


})(this.angular);
