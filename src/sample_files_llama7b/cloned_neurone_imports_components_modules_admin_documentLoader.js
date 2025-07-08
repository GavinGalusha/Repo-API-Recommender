import Utils from '../../globalUtils';
import Configs from '../../globalConfigs';

import { FlowComponents } from '../../../database/flowComponents/index';

import template from './documentLoader.html';
import { ModalCtrl } from '../modal.js';

import axios from 'axios';

class DocumentLoader {
  constructor($scope, $reactive, ModalService, LoadingService) {
    'ngInject';

    $reactive(this).attach($scope);

    this.subscribe('flowComponents');

    this.helpers({
      locales: () => FlowComponents.find({ type: 'locale' }),
      domains: () => FlowComponents.find({ type: 'domain' }),
      tasks: () => FlowComponents.find({ type: 'task' })
    });

    this.doc = {};
    this.route = '';
    this.state = 'wait';
    this.validations= {};
    this.modal = ModalService;
    this.loading = LoadingService;

    this.activateButtonEvaluation();
    console.log('DocumentLoader loaded!');
  }

  downloadDocument() {
    this.state = 'load';

    if (this.form.$valid) {
      this.docObj = this.parseDocumentForm();

      console.log('Document download request sent!', this.docObj);

      this.apply('fetchDocument', [ this.docObj ], { noRetry: true }, (err, res) => {
        if (!err) {
          this.doc = res;
          this.route = res.route;
          this.state = 'show';  
        }
        else {
          console.error('Error while downloading document', err);
          this.doc = {};
          this.route = '';
          this.state = 'error';    
        }
      });
    }
    else {
      console.error('Invalid document form!');
      this.doc = {};
      this.route = '';
      this.state = 'error';
    }
  }

  previewDocument() {
    this.state = 'load';
    
    if (this.form.$valid) {
      this.docObj = this.parseDocumentForm();

      console.log('Document preview request sent!', this.docObj);

      this.apply('previewDocument', [ this.docObj ], { noRetry: true }, (err, res) => {
        if (!err) {
          this.doc = res;
          this.route = res.route;
          this.state = 'show';  
        }
        else {
          console.error('Error while downloading document', err);
          this.doc = {};
          this.route = '';
          this.state = 'error';    
        }
      });
    }
    else {
      console.error('Invalid document form!');
      this.doc = {};
      this.route = '';
      this.state = 'error';
    }
  }

  parseDocumentForm() {
    // TODO check change test-topic
    let form = {
      docName: this.docName,
      title: this.title,
      locale: this.locale || '', //!!(this.locale) ? this.locale[0].properties.code : '',
      relevant: this.relevant || false,
      task: !!this.task ? Utils.forceArray(this.task) : [],
      domain: !!this.domain ? Utils.forceArray(this.domain) : [],
      keywords: !!(this.keywords) && (this.keywords.length > 1) ? this.keywords.split(',').map((kw) => { return kw.trim() }) : [],
      url: this.url,
      maskedUrl: this.maskedUrl,
      searchSnippet: this.snippet || '',
    };

    return form;
  }
  
  changeUrl() {
    if (this.url) {
      document.getElementById("buttonEvaluate").disabled = false;
    } else {
      document.getElementById("buttonEvaluate").disabled = true;
    }
  }

  activateButtonEvaluation() {
    axios.get('http://localhost:8000/ping', {
      responseType: 'json'
    })

    .then(res => {
      if(res.status==200) {
        let data = res.data;
        document.getElementById("buttonEvaluate").disabled = true;
        document.getElementById("buttonEvaluate").className = "btn btn-info pull-right"
        this.validations = data.validations;
      }
    })
    .catch( error => {
      console.error(error);
    });
  }

  callEvaluate(){
    let url = this.url;
    let modalOpts = {
      title: 'Evaluate Compatibility with Screen Readers',
      templateAsset: 'adminAssets/compatibilityService/adminListEvaluations.html',
      buttonType: 'button2',
      buttonName: 'Evaluate',
      fields: {
        url: url,
        evaluations: this.validations
      }
    };
  
    this.modal.openModal(modalOpts, (err, res) => {
      let evals = [];
      if (!err && res.answers) {
        let params = { message: `Loading...` };
        this.loading.start(params);
        let evaluates = Object.keys(res.answers.e);
        for (e in evaluates){
          evals.push(this.validations[evaluates[e]][1]);
        }

        let data = {
          'url' : url,
          'data' : evals
        };
        //console.log("process: ", process); //CS_EVALUATION
        axios.post('http://localhost:8000/petitionEval', data, {
          responseType: 'json'
        }).then(res => {
          console.log("res.status", res.status);
          if(res.status==200) {
            //console.log("process.env: ", process.env);
            //console.log("os.environ: ", os.environ);
            this.resultsEval(res.data);
          }
        })
        .catch( error => {
          this.loading.stop();
          alert('A problem occurred with the compatibility service response.\nSorry for the inconvenience.');
          console.error(error);
        });
      }
    })
  }

  resultsEval(resultsEval){
    let url = resultsEval.data.pop().url;
    let tagsInContent = resultsEval.data.pop().tagsInContent;
    let finalPercent = resultsEval.data.pop().finalPercent;

    let modalOpts = {
      title: 'Results Evaluate Compatibility with Screen Readers',
      templateAsset: 'adminAssets/compatibilityService/adminResultsEvaluations.html',
      buttonType: 'button2',
      buttonName: 'Recomendations',
      fields: {
        url: url,
        tagsInContent: tagsInContent,
        finalPercent: finalPercent,
        data: resultsEval.data
      }
    }

    let data = {
      'data' : resultsEval.data,
      'url': url
    }
    this.loading.stop();
    this.modal.openModal(modalOpts, (err, res) => {
      if (!err) {
        let params = { message: `Loading...` };
        this.loading.start(params);
        this.callRecom(data);
      }
    });
  }

  callRecom(resultsEval){
    axios.post('http://localhost:8000/petitionRecom', resultsEval, {
      responseType: 'json'
    }).then(res => {
      if(res.status==200) {
        this.resultsRecom(res.data.data);
      }
    })
    .catch( error => {
      alert('A problem occurred with the compatibility service response.\nSorry for the inconvenience.');
      console.error(error);
    });
  }

  resultsRecom(resultsRecom){
    let modalOpts = {
      title: 'Recommentations to Incompatibilities with Screen Readers',
      templateAsset: 'adminAssets/compatibilityService/adminResultsRecommendations.html',
      buttonType: 'button',
      buttonName: 'Ok',
      fields: {
        url: this.url,
        data: resultsRecom
      }
    }
    this.loading.stop();
    this.modal.openModal(modalOpts);
  }

}
  
const name = 'documentLoader';

export default angular.module(name, [
])
.component(name, {
  template: template.default,
  controllerAs: name,
  controller: DocumentLoader
});