(function(angular) {
    "use strict";
    angular.module('FileManagerApp').provider("fileManagerConfig", function() {

        var values = {
            appName: "Profireader",
            defaultLang: "en",

            listUrl: "/filemanager/list/",
            uploadUrl: "/filemanager/upload/",
            renameUrl: "/filemanager/rename/",
            set_properties: "/filemanager/properties/",
            search_Url: "/filemanager/search/",
            copyUrl: "/filemanager/copy/",
            cutUrl: "/filemanager/cut/",
            removeUrl: "/filemanager/remove/",
            auto_removeUrl: "/filemanager/auto_remove/",
            editUrl: "bridges/php/handler.php",
            getContentUrl: "bridges/php/handler.php",
            createFolderUrl: "/filemanager/createdir/",
            compressUrl: "bridges/php/handler.php",
            extractUrl: "bridges/php/handler.php",
            permissionsUrl: "bridges/php/handler.php",

            sidebar: true,
            breadcrumb: true,
            allowedActions: {
                rename: !true,
                copy: true,
                edit: !true,
                changePermissions: !true,
                compress: !true,
                compressChooseName: !true,
                extract: !true,
                download: true,
                preview: !true,
                choose: true,
                remove: true
            },

            error_msg_exist:'file_is_not_exist',

            enablePermissionsRecursive: true,
            chunkSize: '512KB',

            isEditableFilePattern: /\.(txt|html?|aspx?|ini|pl|py|md|css|js|log|htaccess|htpasswd|json|sql|xml|xslt?|sh|rb|as|bat|cmd|coffee|php[3-6]?|java|c|cbl|go|h|scala|vb)$/i,
            isImageFilePattern: /\.(jpe?g|gif|bmp|png|svg|tiff?)$/i,
            isExtractableFilePattern: /\.(gz|tar|rar|g?zip)$/i,
            tplPath: 'src/templates'
        };

        return { 
            $get: function() {
                return values;
            }, 
            set: function (constants) {
                angular.extend(values, constants);
            }
        };
    
    });
})(angular);
