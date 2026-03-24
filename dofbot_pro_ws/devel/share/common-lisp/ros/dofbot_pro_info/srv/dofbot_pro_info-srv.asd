
(cl:in-package :asdf)

(defsystem "dofbot_pro_info-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "cur_joint" :depends-on ("_package_cur_joint"))
    (:file "_package_cur_joint" :depends-on ("_package"))
    (:file "dofbot_pro_kinemarics" :depends-on ("_package_dofbot_pro_kinemarics"))
    (:file "_package_dofbot_pro_kinemarics" :depends-on ("_package"))
    (:file "kinemarics" :depends-on ("_package_kinemarics"))
    (:file "_package_kinemarics" :depends-on ("_package"))
  ))