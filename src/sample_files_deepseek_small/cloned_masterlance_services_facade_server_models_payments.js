'use strict'

module.exports = function (Payment) {
  Payment.getBalance = function (accessToken, callback) {
    Payment.app.models.UserAccount.validateToken(accessToken, (err, session) => {
      if (err) return callback(err)
      else if (session) {
        const { userId } = session
        Payment.Wallet_getBalance({
          userId
        }, (err, data) => {
          if (err) callback(err.obj.error)
          else callback(null, data.obj)  
        })
      }
    })
  }
  
  Payment.fetchTransactions = function (accessToken, filters, callback) {
    Payment.app.models.UserAccount.validateToken(accessToken, (err, session) => {
      if (err) return callback(err)
      else if (session) {
        const { userId } = session
        Payment.Wallet_fetchTransactions({
          userId,
          filters
        }, (err, data) => {
          if (err) callback(err.obj.error)
          else callback(null, data.obj)  
        })
      }
    })
  }
 
  Payment.cancelTransaction = function (accessToken, callback) {
    Payment.app.models.UserAccount.validateToken(accessToken, (err, session) => {
      if (err) return callback(err)
      else if (session) {
        Payment.Wallet_cancelTransaction({
          userId: session.userId
        }, (err, data) => {
          if (err) callback(err.obj.error, null)
          else {
            Payment.app.models.Notification.Notification_create({
              data: JSON.stringify({
                title: "Transaction Cancelled",
                body: `You've cancelled the pending top-up transaction`,
                userId: data.obj.to,
                action: "/settings/payments"  
              })
            }, (err, data) => {
              callback(null, data.obj)
            })
          }
        })
      }
    })
  }

  Payment.topupWallet = function (accessToken, amount, callback) {
    Payment.app.models.UserAccount.validateToken(accessToken, (err, session) => {
      if (err) return callback(err.obj.error)
      else if (session) {
        const { userId } = session
        Payment.Wallet_topup({
          userId,
          amount
        }, (err, data) => {
          if (err) callback(err.obj.error)
          else {
            callback(null, data.obj)
          }
        })
      }
    })
  }
  
  Payment.verify = function (params, callback) {
    Payment.Transaction_verifyTransaction({
      params: JSON.stringify(params)
    }, (err, data) => {
      if (err) callback(err.obj.error)
      else {
        // {
        //  dateTime: '',
        //  reason: '',
        //  amount: 1,
        //  from: 'external (YenePay)',
        //  to: '',
        //  status: 'COMPLETE',
        //  type: 'TOPUP',
        //  id: '',
        // }
        Payment.app.models.Notification.Notification_create({
          data: JSON.stringify({
            title: "Transaction Completed",
            body: `${data.obj.amount} Birr has been added to your wallet.`,
            userId: data.obj.to,
            action: "/settings/payments"  
          })
        }, (err, data) => {
          callback(null, data.obj)
        })
      }
    })
  }
}


