**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zget_assigned_robot_who .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"  EXPORTING
*"     REFERENCE(ET_WO_RSRC_TY) TYPE  /SCWM/TT_WO_RSRC_TY
*"----------------------------------------------------------------------

* Get Warehouse Orders which are assigned to the robot ressource
  select * from /scwm/wo_rsrc_ty
    where
      lgnum = @iv_lgnum and
      rsrc = @iv_rsrc
    order by lsd ascending, priority descending
    into table @et_wo_rsrc_ty.

  if sy-subrc <> 0.
    clear et_wo_rsrc_ty.
  endif.

endfunction.
