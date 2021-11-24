const verify_secrets = require('./verify_secrets');

test('throws invalid number', async () => {
  await expect('foo').toBe('foo')
});

test('throws invalid number', async () => {
  // Arrange
  var secretsObj = new Object();
  secretsObj.SECRET_1 = "SECRET_1_VALUE";
  secretsObj.SECRET_2 = "SECRET_2_VALUE";
  var secretsJson = JSON.stringify(secretsObj);

  // Act
  await verify_secrets(secretsJson);
  // Assert

});
