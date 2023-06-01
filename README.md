# fastapi-filterstyles

## Introduction
`fastapi-filterstyles` is a library I put together to simplify a lot of the boilerplate
code I found myself writing across multiple applications.

Commonly in data-heavy applications I found myself writing a list endpoint, and then wanting to be able to filter on that list endpoint. 
Filtering in query strings can be complex and there are a variety of styles for doing so, and I was finding myself writing the same code over and over.

This library attempts to simplify and standardise the generation of filter query strings, while making the data passed into the route transparent to how it was generated.

Currently the library supports both delimited styles, e.g. `?name=contains:shell&name=neq:shell+beach` and the OpenAPI [deep object style](https://swagger.io/docs/specification/serialization/) `?name[contains]=shell&name[neq]=shell+beach`.

## Usage

### Filter class

Irregardless of style, the first thing to do is build your filter class. This is a Pydantic object that represents the filters you want to accept. It can contain any combination of standard library types such as `bool`, `int` and `str`, as well as fields that inherit from the `BaseFilter` class of this package. The package only provides a few at the moment, with more to come as I add them.

Because BaseFilters are also Pydantic objects, the data parsing functionality works identically, and will generate a human-readable set of errors should the parsing fail (e.g. passing a random string to a UUID field).

Each filter class provides a set of possible operations, such as `eq`, `neq`, `contains`. If you want to only expose a subset of these on a given field, you can pass that information into the field on the filter class. If no subset is provided, all operators for that type will be accepted.

```python
from fastapi_filterstyles import StringFilter, UUIDFilter
from pydantic import BaseModel, Field

class ItemFilters(BaseModel):
    id: UUIDFilter
    name: StringFilter = Field(operators=["eq", "neq"])
    active: bool | None = None
```

### Dependency

Once you have your filter class, you can then use either `deep_object_filter()` or `delimited_filter()` to create your dependency for the route. In this case I've used the `Annotated` syntax as recommended by the FastAPI project, but the older `= Depends()` syntax should be supported as well.

If using the `deep_object_filter` style you must also pass your app instance to the `update_deep_objects()` method once all the routes are loaded. This updates the OpenAPI schema to correctly notate the deep object style. You can skip this step if you aren't using the OpenAPI schema.

You can then access all of the fields on the returned filters object just as you would any other Pydantic model.

```python
@app.get("/items")
async def items(filters: Annotated[ItemFilters, Depends(deep_object_filter(ItemFilters)]):
    items = get_all_my_items()
    return [i for i in items if i.name in filters.name.eq]

update_deep_objects(app)
```

