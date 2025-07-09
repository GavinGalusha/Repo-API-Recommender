import fs from 'fs';
import path from 'path';
import glob from 'glob';

import Utils from '../utils/serverUtils';

import { FormQuestions } from '../../imports/database/formQuestions/index';
import { FormQuestionnaires } from '../../imports/database/formQuestionnaires/index';
import { SynthesisQuestions } from '../../imports/database/synthesisQuestions/index';
import { Settings } from '../../imports/database/settings/index';

export default class ContentLoader {
  // dgacitua: This method will load all your questions, questionnaires and synthesis questions to NEURONE database
  //           Files are read from neuroneAssets/questions/*.json
  //           See the documentation for proper format for these elements
  static loadQuestions(assetPath) {
    try {
      let fullPath = path.join(assetPath, 'questions', '*.json');

      if (fs.existsSync(fullPath)) {
        let files = glob.sync(fullPath),
            total = files.length;

        files.forEach((file, idx, arr) => {
          var fn = path.basename(file);
          console.log('Reading question file!', '[' + (idx+1) + '/' + total + ']', fn);

          var questionFile = fs.readFileSync(file),
           loadedQuestions = JSON.parse(questionFile);          

          loadedQuestions.forEach((q) => {
            // TODO Question format parser and validator
            if (q.questionId) {
              FormQuestions.upsert({ questionId: q.questionId }, q);
            }
            else if (q.questionnaireId) {
              FormQuestionnaires.upsert({ questionnaireId: q.questionnaireId }, q);
            }
            else if (q.synthesisId) {
              SynthesisQuestions.upsert({ synthesisId: q.synthesisId }, q);
            }
            else {
              console.warn('Wrong question format detected in object');
            }
          });
        });
      }

      return true;
    }
    catch (err) {
      console.error(err);
      throw new Meteor.Error(521, 'Cannot load questions from file!', err);
    }
  }

  // dgacitua: This method will load all your environment settings, client settings and flow settings to NEURONE database
  //           Files are read from public/default/userSettings.json and neuroneAssets/userSettings.json
  //           See the documentation for proper format for these elements
  static loadSettings(assetPath) {
    try {
      let defaultFile = path.join(Utils.getPublicFolder(), 'default', 'userSettings.json'),
             fullPath = path.join(assetPath, 'userSettings.json');

      if (fs.existsSync(defaultFile)) {
        console.log('Reading default settings!');

        var settingsFile = fs.readFileSync(defaultFile),
          loadedSettings = JSON.parse(settingsFile);

        loadedSettings.forEach((s) => {
          // TODO Config format parser and validator
          if (s.flowSettingsId) {
            Settings.upsert({ flowSettingsId: s.flowSettingsId }, s);
          }
          else if (s.clientSettingsId) {
            Settings.upsert({ clientSettingsId: s.clientSettingsId }, s);
          }
          else if (s.envSettingsId) {
            Settings.upsert({ envSettingsId: s.envSettingsId }, s);
          }
          else {
            console.warn('Wrong settings format detected in object');
          }
        });
      }
      else {
        console.warn('Could not read default settings!');
      }

      if (fs.existsSync(fullPath)) {
        let files = glob.sync(fullPath),
            total = files.length;

        files.forEach((file, idx, arr) => {
          var fn = path.basename(file);
          console.log('Reading settings file!', '[' + (idx+1) + '/' + total + ']', fn);

          var settingsFile = fs.readFileSync(file),
            loadedSettings = JSON.parse(settingsFile);

          loadedSettings.forEach((s) => {
            // TODO Config format parser and validator
            if (s.flowSettingsId) {
              Settings.upsert({ flowSettingsId: s.flowSettingsId }, s);
            }
            else if (s.clientSettingsId) {
              Settings.upsert({ clientSettingsId: s.clientSettingsId }, s);
            }
            else if (s.envSettingsId) {
              Settings.upsert({ envSettingsId: s.envSettingsId }, s);
            }
            else {
              console.warn('Wrong settings format detected in object');
            }
          });
        });

        return true;
      }
      else {
        return true;
      }
    }
    catch (err) {
      console.error(err);
      throw new Meteor.Error(522, 'Cannot load settings from file!', err);
    }
  }
}