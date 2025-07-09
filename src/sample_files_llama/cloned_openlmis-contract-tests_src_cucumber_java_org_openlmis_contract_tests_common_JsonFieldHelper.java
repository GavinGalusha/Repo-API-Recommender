/*
 * This program is part of the OpenLMIS logistics management information system platform software.
 * Copyright © 2017 VillageReach
 *
 * This program is free software: you can redistribute it and/or modify it under the terms
 * of the GNU Affero General Public License as published by the Free Software Foundation, either
 * version 3 of the License, or (at your option) any later version.
 *  
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
 * See the GNU Affero General Public License for more details. You should have received a copy of
 * the GNU Affero General Public License along with this program. If not, see
 * http://www.gnu.org/licenses.  For additional information contact info@OpenLMIS.org. 
 */

package org.openlmis.contract_tests.common;

import org.json.simple.JSONObject;

public final class JsonFieldHelper {

  public static Object getField(JSONObject json, String path) {
    int dotIndex = path.indexOf('.');
    boolean nestedField = -1 != dotIndex;

    if (nestedField) {
      String field = path.substring(0, dotIndex);
      String rest = path.substring(dotIndex + 1);
      JSONObject subJson = getSubJson(json, field);

      return getField(subJson, rest);
    } else {
      return json.get(path);
    }
  }

  public static void setField(JSONObject json, String path, Object value) {
    int dotIndex = path.indexOf('.');
    boolean nestedField = -1 != dotIndex;

    if (nestedField) {
      String field = path.substring(0, dotIndex);
      String rest = path.substring(dotIndex + 1);
      JSONObject subJson = getSubJson(json, field);

      setField(subJson, rest, value);
    } else {
      json.put(path, value);
    }
  }

  private static JSONObject getSubJson(JSONObject json, String field) {
    if (!json.containsKey(field)) {
      json.put(field ,new JSONObject());
    }

    return (JSONObject) json.get(field);
  }

}
