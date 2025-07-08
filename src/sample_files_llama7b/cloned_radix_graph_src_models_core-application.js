const mongoose = require('../connections/mongoose/core');
const schema = require('../schema/core-application');

module.exports = mongoose.model('core-application', schema);
