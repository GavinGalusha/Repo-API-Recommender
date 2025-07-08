import { Meteor } from 'meteor/meteor';
import ip from 'ip';
import UserAgent from 'useragent';

import Utils from '../utils/serverUtils';

import { UserData, Settings, Identities, FlowComponents, FlowElements } from '../database/definitions';

// NEURONE API: Configs Getter
// Methods for getting settings for users from the server

Meteor.methods({
  // dgacitua: Get user data from its userId
  //           PARAMS: userId (ID in database for the questionnaire)
  //           RETURNS: Meteor User data
  userDataFromId: function(userId) {
    // dgacitua: Server-only method
    // https://github.com/themeteorchef/server-only-methods
    try {
      check(userId, String);

      console.log(Meteor.users.findOne({ _id: userId }).username);
      if (this.connection == null) return Meteor.users.findOne({ _id: userId });
      else return undefined;
    }
    catch (err) {
      throw new Meteor.Error(531, 'Could not get User Data from userId!', err);
    }
  },
  // dgacitua: Get user role from logged client
  //           PARAMS: <none>
  //           RETURNS: <String>
  userRole: function() {
    try {
      if (this.userId) {
        return UserData.findOne({ userId: this.userId }).role;
      }
      else {
        return '';
      }
    }
    catch (err) {
      throw new Meteor.Error(532, 'Could not read user session!', err);
    }
  },
  // dgacitua: Get user session (temporal state variables) from logged user
  //           PARAMS: <none>
  //           RETURNS: Session JSON object
  userSession: function() {
    try {
      if (this.userId) {
        return UserData.findOne({ userId: this.userId }).session;
      }
      else {
        return {};
      }
    }
    catch (err) {
      throw new Meteor.Error(533, 'Could not read user session!', err);
    }
  },
  // dgacitua: Get user configs (flow execution data) from logged user
  //           PARAMS: <none>
  //           RETURNS: Configs JSON object
  userConfigs: function() {
    try {
      if (this.userId) {
        return UserData.findOne({ userId: this.userId }).configs;
      }
      else {
        return {};
      }
    }
    catch (err) {
      throw new Meteor.Error(534, 'Could not read user configs!', err);
    }
  },
  // dgacitua: Set user session (temporal state variables) from logged client and return them
  //           PARAMS: properties (JSON key-value object with session variables)
  //           RETURNS: Session JSON object
  setSession: function(properties) {
    try {
      if (this.userId) {
        var setObj = {};

        for (var key in properties) {
          setObj['session.' + key] = properties[key];
        }
        
        UserData.update({ userId: this.userId }, { $set: setObj });
        
        return UserData.findOne({ userId: this.userId }).session;
      }
    }
    catch (err) {
      throw new Meteor.Error(535, 'Could not update user session!', err);
    }
  },
  // dgacitua: Get initial user configs for new created user from client
  //           PARAMS: domain (flow domain as String) & task (flow task as String)
  //           RETURNS: Flow Settings JSON object
  initialConfigs: function(locale, task, domain) {
    try {
      var envSettings = Settings.findOne({ envSettingsId: 'default' }),
         flowSettings = null;

      if (!!locale && !!task && !!domain) {
        flowSettings = FlowElements.findOne({ type: 'flow', locale: locale, task: task, domain: domain });
      }
      else {
        flowSettings = Settings.findOne({ flowSettingsId: envSettings.flowSettings }); 
      }

      delete flowSettings._id;

      return flowSettings;
    }
    catch (err) {
      throw new Meteor.Error(536, 'Could not read initial user configs!', err);
    }
  },
  // dgacitua: Get client settings (basic configs for NEURONE simulation) from client
  //           PARAMS: <none>
  //           RETURNS: Client Settings JSON object
  clientSettings: function() {
    try {
      var envSettings = Settings.findOne({ envSettingsId: 'default' }),
       clientSettings = Settings.findOne({ clientSettingsId: envSettings.clientSettings });

      delete clientSettings._id;

      return clientSettings;
    }
    catch (err) {
      throw new Meteor.Error(537, 'Could not read NEURONE client configs!', err);
    }
  },
  // dgacitua: Massive enrollment method for creating multiple user accounts
  //           PARAMS: userList (JSON array of user credentials)
  //           RETURNS: Updated userList with registration status
  registerUsers: function(userList) {
    check(userList, Array);

    userList.forEach((user, idx, arr) => {
      let tempCredentials = {
        username: user.username,
        password: user.password,
        role: 'student',
        configs: {},
        session: {},
        profile: {}
      };

      let studyFlow = FlowElements.findOne({ type: 'flow', locale: user.locale, domain: user.domain, task: user.task });

      if (!(!!studyFlow)) {
        arr[idx].status = 'ConfigError';
      }
      else {
        tempCredentials.configs = studyFlow;

        let id = Accounts.createUser(tempCredentials);
        
        if (!(!!id)) {
          arr[idx].status = 'RegisterError';
        }
        else {
          arr[idx].status = 'Registered';
        }
      }

      /*
      if (user.domain === 'SS') domain = 'social';
      else if (user.domain === 'SC') domain = 'science';
      else domain = 'pilot';

      if (user.task === 'E') task = 'email';
      else if (user.task === 'A') task = 'article';
      else task = 'pilot';

      flowSettings = Settings.findOne({ task: task, domain: domain });

      if (!(!!flowSettings)) {
        arr[idx].status = 'ConfigError';
      }
      else {
        tempCredentials.configs = flowSettings;

        let id = Accounts.createUser(tempCredentials);

        if (!(!!id)) {
          arr[idx].status = 'RegisterError';
        }
        else {
          arr[idx].status = 'Registered';
        }
      }
      */
    });

    return userList;
  },
  // dgacitua: Save user's real name obtained from login (this data is just for reference purposes)
  //           PARAMS: id (user's real name as String)
  //           RETURNS: Identity JSON object
  registerIdentity: function(id) {
    try {
      check(id, String);

      if (this.userId) {
        var time = Utils.getTimestamp();

        var identity = {
          userId: this.userId,
          username: Meteor.user().username,
          identity: id,
          serverDate: Utils.timestamp2date(time),
          serverTime: Utils.timestamp2time(time),
          serverTimestamp: time
        };

        var result = Identities.insert(identity);
       
        if (!!result) return identity;
        else return false;
      }
    }
    catch (err) {
      console.error(err);
      throw new Meteor.Error(538, 'Could not register new user!', err);
    }
  },
  getServerStats: function(localTimestamp) {
    try {
      check(localTimestamp, Match.Maybe(Number));

      let ipAddr = this.connection ? this.connection.clientAddress : '',
             rua = this.connection ? this.connection.httpHeaders['user-agent'] : '',   // raw user agent
             oua = rua ? UserAgent.parse(rua) : '',               // object user agent
         browser = oua ? oua.toAgent() : 'undefined',
              os = oua ? oua.os.toString() : 'undefined',
          device = oua ? oua.device.toString() : 'undefined';

      let serverTimestamp = Utils.getTimestamp(),
                pingValue = !!localTimestamp ? (serverTimestamp - localTimestamp) : null;

      let response = {
        serverTime: Utils.timestamp2date(serverTimestamp) + ' ' + Utils.timestamp2time(serverTimestamp),
        serverIpAddr: ip.address(),
        clientUserAgent: rua,
        clientIpAddr: ipAddr,
        clientBrowser: browser,
        clientOperatingSystem: os,
        clientDevice: device,
        ping: pingValue
      };

      return response;
    }
    catch (err) {
      console.error(err);
      throw new Meteor.Error(539, 'Could not get server statistics!', err);
    }
  }
});